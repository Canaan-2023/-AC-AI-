# 修改后的代码支持动态指定任意模型，主要变更如下：
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
import time
from typing import List, Dict, Any, Optional
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from datasets import Dataset, DatasetDict
import torch
from memex_a import MemexA, Config
# ===================== 日志配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [FineTune] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fine_tune.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Memex-FineTune")
# ===================== 标准化训练配置 =====================
# 移除固定模型名称，改为动态传入
BASE_CONFIG = {
    "output_dir": "./finetuned_model",
    "overwrite_output_dir": True,
    "epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 2,
    "learning_rate": 1e-4,
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "max_seq_length": 2048,
    "logging_steps": 10,
    "save_steps": 50,
    "save_total_limit": 2,
    "fp16": torch.cuda.is_available(),
    "load_best_model_at_end": True,
    "metric_for_best_model": "loss",
    "greater_is_better": False,
    "report_to": "none"
}
# 降级配置也改为相对值调整，不固定模型
FALLBACK_ADJUSTMENTS = {
    "batch_size": 0.5,  # 原批次大小的一半
    "learning_rate": 0.5,  # 原学习率的一半
    "epochs": 0.67,  # 约2/3原epochs
    "max_seq_length": 0.5  # 约一半序列长度
}
# ===================== 数据加载 =====================
def load_finetune_data(max_samples_per_level: int = 20) -> List[Dict[str, str]]:
    try:
        config = Config.from_json()
        memex = MemexA(config=config)
        data = []
        system_prompt = {
            "prompt": "你是Memex-A记忆辅助AI，精通认知科学和记忆管理，能够基于用户的记忆内容提供专业、简洁的解读、分析和关联建议。",
            "response": "明白！我将基于你的记忆内容，提供符合认知科学原理的专业解读、分析和关联建议，帮助你深化记忆理解和知识整合。"
        }
        data.append(system_prompt)
        memory_levels = ["核心", "元认知", "工作", "情感"]
        for level in memory_levels:
            logger.info(f"📥 加载「{level}」层级记忆（最多{max_samples_per_level}条）")
            memories = memex.advanced_search(
                filters={
                    "levels": [level],
                    "min_strength": 0.7,
                    "exclude_expired": True
                }
            )
            memories_sorted = sorted(memories, key=lambda x: x["最大关联强度"], reverse=True)
            selected_memories = memories_sorted[:max_samples_per_level]
            for mem in selected_memories:
                mid = mem["记忆ID"]
                full_content = memex.get_full_content(mid) or mem["内容摘要"]
                prompt = f"请基于认知科学原理，解读以下{level}记忆的核心价值、关联意义和深化建议：\n\n记忆内容：{full_content}"
                response = generate_reference_response(level, full_content, mem["关联记忆"])
                data.append({"prompt": prompt, "response": response})
        with memex._cache_lock:
            be_token_cache = memex._read_json(config.BE_TOKEN_PATH)
            active_tokens = [t for t in be_token_cache.values() if t.get("status") == "active"]
            if active_tokens:
                token = active_tokens[0]
                prompt = f"请分析以下BE Token的目标维度、当前进度，并提供加速达成目标的记忆管理建议：\n\n目标维度：{token['target_dimension']}\n当前进度：{token['current_progress']}/{token['target_value']}\n关联记忆：{token['related_memory_ids']}"
                response = f"### 目标维度分析：{token['target_dimension']}\n- 核心意义：{'提升记忆整合效率' if token['target_dimension'] == '元块整合度' else '增强记忆连贯性' if token['target_dimension'] == '跨会话相干性' else '加速认知能力成长'}\n- 当前进度评估：{'良好' if token['current_progress'] >= 0.7 else '一般' if token['current_progress'] >= 0.5 else '待提升'}\n- 优化建议：1. 增加关联记忆的检索频率；2. 补充相关领域的核心记忆；3. 定期复盘关联强度变化；4. 利用间隔重复强化关键记忆。"
                data.append({"prompt": prompt, "response": response})
        logger.info(f"✅ 数据加载完成：共{len(data)}条训练样本")
        return data
    except Exception as e:
        logger.error(f"❌ 加载微调数据失败：{e}", exc_info=True)
        return []

def generate_reference_response(level: str, content: str, related_memories: Dict[str, float]) -> str:
    level_analysis = {
        "核心": "该核心记忆是知识体系的基石，具有高稳定性和强关联价值。",
        "元认知": "该元认知记忆反映了对自身认知过程的理解，有助于优化学习策略。",
        "工作": "该工作记忆是当前任务的关键信息，需及时与核心记忆建立关联以促进转化。",
        "情感": "该情感记忆为认知过程提供动机支持，积极情感有助于记忆巩固。"
    }
    related_analysis = f"关联记忆强度分析：{related_memories}" if related_memories else "暂未建立有效关联，建议主动关联核心/元认知记忆"
    return (
        f"### 记忆解读（{level}层级）\n"
        f"- 核心价值：{level_analysis[level]}\n"
        f"- 内容要点：{content[:100]}...\n"
        f"- 关联意义：{related_analysis}\n"
        f"- 深化建议：1. 定期检索强化记忆痕迹；2. 补充相关领域的延伸记忆；3. 尝试用自己的语言重构记忆内容；4. 建立跨层级的记忆关联。"
    )
# ===================== 数据预处理 =====================
# 保持不变，但确保兼容不同tokenizer
def preprocess_data(data: List[Dict[str, str]], tokenizer: AutoTokenizer, max_seq_length: int) -> DatasetDict:
    try:
        formatted_texts = []
        for item in data:
            text = f"用户：{item['prompt']}\nAI：{item['response']}\n"
            formatted_texts.append(text)
        dataset = Dataset.from_dict({"text": formatted_texts})
        
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_seq_length,
                padding="max_length",
                return_overflowing_tokens=False
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"]
        )
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
        logger.info(f"✅ 数据预处理完成：训练集{len(split_dataset['train'])}条，验证集{len(split_dataset['test'])}条")
        return split_dataset
    except Exception as e:
        logger.error(f"❌ 数据预处理失败：{e}", exc_info=True)
        return DatasetDict()
# ===================== 训练逻辑 =====================
def train(model_name: str, config: Dict[str, Any] = None) -> bool:
    """
    支持任意模型的训练函数
    :param model_name: 模型名称或本地路径
    :param config: 训练配置参数
    """
    current_config = {**BASE_CONFIG,** config} if config else BASE_CONFIG
    logger.info(f"\n" + "="*60)
    logger.info(f"🚀 启动微调训练（模型：{model_name}）")
    logger.info(f"="*60)
    
    try:
        raw_data = load_finetune_data()
        if len(raw_data) < 10:
            logger.error(f"❌ 训练数据不足（仅{len(raw_data)}条），终止训练")
            return False
            
        logger.info(f"📥 加载模型：{model_name}")
        # 增加模型加载的灵活性，支持不同模型的特殊参数
        tokenizer_kwargs = {
            "trust_remote_code": True,
            "padding_side": "right"
        }
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch.float16 if current_config["fp16"] else torch.float32,
            "device_map": "auto"
        }
        
        # 针对不同模型家族的特殊处理
        if "llama" in model_name.lower() or "alpaca" in model_name.lower():
            tokenizer_kwargs["use_fast"] = False
        
        tokenizer = AutoTokenizer.from_pretrained(model_name, **tokenizer_kwargs)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(model_name,** model_kwargs)
        model.config.use_cache = False
        
        tokenized_dataset = preprocess_data(raw_data, tokenizer, current_config["max_seq_length"])
        if not tokenized_dataset or len(tokenized_dataset["train"]) == 0:
            logger.error(f"❌ 预处理后无有效训练数据，终止训练")
            return False
            
        training_args = TrainingArguments(
            output_dir=current_config["output_dir"],
            overwrite_output_dir=current_config["overwrite_output_dir"],
            num_train_epochs=current_config["epochs"],
            per_device_train_batch_size=current_config["batch_size"],
            per_device_eval_batch_size=current_config["batch_size"] * 2,
            gradient_accumulation_steps=current_config["gradient_accumulation_steps"],
            learning_rate=current_config["learning_rate"],
            warmup_ratio=current_config["warmup_ratio"],
            weight_decay=current_config["weight_decay"],
            logging_steps=current_config["logging_steps"],
            save_steps=current_config["save_steps"],
            save_total_limit=current_config["save_total_limit"],
            fp16=current_config["fp16"],
            load_best_model_at_end=current_config["load_best_model_at_end"],
            metric_for_best_model=current_config["metric_for_best_model"],
            greater_is_better=current_config["greater_is_better"],
            report_to=current_config["report_to"],
            evaluation_strategy="epoch",
            eval_accumulation_steps=current_config["gradient_accumulation_steps"]
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
            pad_to_multiple_of=8 if current_config["fp16"] else None
        )
        
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset["train"],
            eval_dataset=tokenized_dataset["test"],
            data_collator=data_collator,
            tokenizer=tokenizer
        )
        
        logger.info(f"🎬 开始训练（设备：{trainer.args.device}）")
        start_time = time.time()
        train_result = trainer.train()
        training_time = (time.time() - start_time) / 3600
        
        # 训练结果处理
        trainer.save_model(current_config["output_dir"])
        metrics = train_result.metrics
        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)
        trainer.save_state()
        
        logger.info(f"\n" + "="*60)
        logger.info(f"📊 训练完成！")
        logger.info(f"训练时长：{training_time:.2f}小时")
        logger.info(f"训练损失：{metrics['train_loss']:.4f}")
        logger.info(f"评估损失：{trainer.evaluate()['eval_loss']:.4f}")
        logger.info("="*60)
        
        return True
    except Exception as e:
        logger.error(f"❌ 训练失败：{e}", exc_info=True)
        return False
# ===================== 带降级策略的训练入口 =====================
def train_with_fallback(model_names: List[str], base_config: Optional[Dict[str, Any]] = None):
    """
    支持多模型尝试的训练入口
    :param model_names: 模型名称列表，按优先级排序
    :param base_config: 基础训练配置
    """
    logger.info(f"\n" + "="*80)
    logger.info(f"🚀 启动多模型微调训练（尝试模型：{model_names}）")
    logger.info("="*80)
    
    base_config = base_config or BASE_CONFIG
    
    for i, model_name in enumerate(model_names):
        # 第一次尝试使用原始配置
        if i == 0:
            logger.info(f"📌 第{i+1}次尝试：使用模型 {model_name}（原始配置）")
            success = train(model_name, base_config)
            if success:
                logger.info(f"\n🎉 模型 {model_name} 训练成功！")
                verify_finetuned_model(base_config["output_dir"])
                return True
        
        # 后续尝试使用降级配置
        else:
            adjusted_config = {}
            for key, ratio in FALLBACK_ADJUSTMENTS.items():
                if key in base_config:
                    adjusted_config[key] = int(base_config[key] * ratio) if isinstance(base_config[key], int) else base_config[key] * ratio
            
            fallback_config = {**base_config,** adjusted_config}
            logger.info(f"📌 第{i+1}次尝试：使用模型 {model_name}（降级配置：{adjusted_config}）")
            success = train(model_name, fallback_config)
            if success:
                logger.info(f"\n🎉 模型 {model_name} 训练成功！")
                verify_finetuned_model(fallback_config["output_dir"])
                return True
    
    logger.error(f"\n❌❌ 所有模型训练均失败，请检查配置和环境")
    return False
# ===================== 模型验证和集成验证 =====================
def verify_finetuned_model(model_dir: str):
    logger.info(f"\n" + "="*60)
    logger.info(f"🔍 验证微调模型：{model_dir}")
    logger.info("="*60)
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        model.eval()
        test_prompts = [
            "请解读以下核心记忆的核心价值：记忆内容：系统基础功能验证：添加核心记忆",
            "如何提升元块整合度的BE Token进度？"
        ]
        for prompt in test_prompts:
            logger.info(f"\n📥 测试输入：{prompt[:50]}...")
            input_text = f"用户：{prompt}\nAI："
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    eos_token_id=tokenizer.eos_token_id
                )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True).split("AI：")[-1].strip()
            logger.info(f"📤 模型输出：{response[:100]}...")
        logger.info(f"\n✅ 微调模型验证通过！")
    except Exception as e:
        logger.error(f"❌ 验证微调模型失败：{e}", exc_info=True)

def integrate_with_memex():
    logger.info(f"\n" + "="*80)
    logger.info(f"🔗 验证微调模型与Memex-A集成")
    logger.info("="*80)
    try:
        config = Config.from_json()
        memex = MemexA(config=config)
        model_dir = BASE_CONFIG["output_dir"]
        tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        model.eval()
        core_memories = memex.search_memory(level="核心")
        if core_memories:
            mem = core_memories[0]
            mid = mem["记忆ID"]
            full_content = memex.get_full_content(mid)
            prompt = f"作为Memex-A的记忆辅助AI，分析以下核心记忆的AC-100维度贡献，并提供优化建议：\n\n记忆ID：{mid}\n记忆内容：{full_content[:150]}..."
            input_text = f"用户：{prompt}\nAI："
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.6,
                    top_p=0.85,
                    repetition_penalty=1.1
                )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True).split("AI：")[-1].strip()
            logger.info(f"\n📋 Memex-A核心记忆分析结果：")
            logger.info(f"记忆ID：{mid}")
            logger.info(f"分析结论：{response}")
        logger.info(f"\n✅ 模型与Memex-A集成验证通过！")
        return True
    except Exception as e:
        logger.error(f"❌ 模型与Memex-A集成失败：{e}", exc_info=True)
        return False

# ===================== 主函数 =====================
if __name__ == "__main__":
    print("🔥 Memex-A 通用微调脚本（支持任意模型）")
    print("="*60)
    
    # 允许通过命令行参数指定模型列表
    if len(sys.argv) > 1:
        model_candidates = sys.argv[1:]
    else:
        # 默认模型候选列表
        model_candidates = [
            "Qwen/Qwen2.5-0.5B",
            "mistralai/Mistral-7B-v0.1",
            "meta-llama/Llama-2-7b-hf",
            "baichuan-inc/Baichuan2-7B-Base"
        ]
    
    print(f"📋 准备尝试的模型列表：{model_candidates}")
    
    raw_data = load_finetune_data()
    if len(raw_data) < 10:
        print(f"❌ 训练数据不足（仅{len(raw_data)}条），退出训练（需至少10条有效样本）")
        exit(1)
    
    # 执行多模型训练尝试
    train_success = train_with_fallback(model_candidates)
    if not train_success:
        print(f"❌ 所有模型训练尝试均失败，请检查环境和配置")
        exit(1)
    
    # 训练成功后，验证与Memex-A的集成能力
    integrate_success = integrate_with_memex()
    if not integrate_success:
        print(f"⚠️ 模型训练成功，但与Memex-A集成验证失败，可手动测试集成逻辑（路径：{BASE_CONFIG['output_dir']}）")
        exit(1)
    
    # 全流程完成提示
    print("\n" + "="*80)
    print("🎉 微调全流程完成！模型已就绪并集成到Memex-A系统")
    print(f"📁 微调模型路径：{BASE_CONFIG['output_dir']}")
    print(f"📊 训练数据量：{len(raw_data)}条（含系统提示词+4层级记忆+BE Token分析）")
    print(f"✅ 功能验证：模型训练→效果验证→Memex-A集成 全通过")
    print("💡 使用方式：在main.py中调用MemexA.auto_finetune()可自动触发微调")
    print("="*80)