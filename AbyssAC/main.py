import os
import time
import logging
import json
from datetime import datetime
# 导入系统核心模块（复用原版依赖）
from memex_a import MemexA
from x_y_loader import xy_loader
from consciousness_emerge import ConsciousnessEmerge
from endogenous_iter import EndogenousIteration
from fine_tune import train_with_fallback, integrate_with_memex
from fine_tune import BASE_CONFIG as FINE_TUNE_CONFIG

# ===================== 初始化日志（新增：记录所有操作） =====================
LOG_DIR = "./memex_logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f"memex_main_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8"),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger("memex_main")

# ===================== 工具函数（新增：通用校验/格式化） =====================
def validate_mem_id(mem_id: str) -> bool:
    """验证记忆ID格式（非空+数字/字母组合）"""
    if not mem_id.strip():
        return False
    return mem_id.strip().replace("_", "").isalnum()

def format_time(elapsed: float) -> str:
    """格式化耗时（保留2位小数）"""
    return f"{elapsed:.2f}秒"

def print_separator(char="-", length=50):
    """打印分隔线"""
    print(char * length)

# ===================== 核心交互函数（完善原版逻辑） =====================
def run():
    """完整版交互主函数（含全异常处理+输入校验+日志）"""
    print("="*60)
    print("🔥 渊协议v5.2（完整版）启动中...")
    print("="*60)
    
    # 1. 初始化核心组件（原版逻辑+异常强化）
    memex = None
    emerge_module = None
    endogenous_module = None
    try:
        memex = MemexA()
        emerge_module = ConsciousnessEmerge(memex)
        endogenous_module = EndogenousIteration(memex)
        logger.info("所有核心组件初始化完成")
        print("✅ 核心组件初始化完成（MemexA/意识涌现/内生迭代）")
    except Exception as e:
        logger.error(f"组件初始化失败：{str(e)}", exc_info=True)
        print(f"❌ 初始化失败：{str(e)}")
        input("按回车退出...")
        return
    
    # 2. 显示完整版指令说明（新增：帮助指令基础）
    print("\n" + "="*80)
    print("📌 渊协议v5.2 完整版指令列表（大小写不敏感）：")
    print("  基础操作：")
    print("    新增记忆 [层级] [内容] [关联ID(可选)] [范畴标签(可选)] - 示例：新增记忆 核心 渊协议核心原则  🔶")
    print("    修改记忆 [ID] [新内容] - 示例：修改记忆 1 渊协议核心原则：认知自动化")
    print("    删除记忆 [ID] - 示例：删除记忆 1")
    print("    导出记忆 [ID1,ID2] [路径] - 示例：导出记忆 1,2 ./backup.json")
    print("  检索操作：")
    print("    检索记忆 [关键词] [层级(可选)] - 示例：检索记忆 核心原则 核心")
    print("    检索范畴 [符号] - 示例：检索范畴 ▶（▶=1-态射，⚠=2-态射，📌=弱等价）")
    print("  高阶操作：")
    print("    AC100自检 - 8维度完整认知评估（含元块整合度）")
    print("    意识涌现验证 - 检查Φ值+跨会话相干性，触发X层更新")
    print("    内生迭代 - AC100≥80分时优化元认知记忆")
    print("    模型微调 [模型名] - 示例：模型微调 Qwen/Qwen2.5-0.5B")
    print("  辅助操作：")
    print("    帮助 - 重新显示指令列表")
    print("    退出 - 自动备份数据并关闭系统")
    print("="*80)
    
    # 3. 交互循环（原版逻辑+全维度强化）
    while True:
        cmd_input = input("\n请输入指令：").strip().lower()  # 新增：大小写不敏感
        if not cmd_input:  # 新增：空输入校验
            print("❌ 指令不能为空！输入「帮助」查看可用指令")
            continue
        
        # 记录指令日志
        logger.info(f"用户输入指令：{cmd_input}")
        start_time = time.time()  # 新增：耗时统计
        
        try:
            # 3.1 退出（原版逻辑+自动备份+日志）
            if cmd_input == "退出":
                print("\n📤 正在自动备份数据...")
                backup_path = memex.create_backup(compress=True)
                logger.info(f"系统退出，数据备份至：{backup_path}")
                print(f"✅ 数据已备份至：{backup_path}")
                print("\n👋 渊协议v5.2已安全退出")
                print("="*60)
                break
            
            # 3.2 帮助（新增：重新显示指令）
            elif cmd_input == "帮助":
                print("\n" + "="*80)
                print("📌 渊协议v5.2 完整版指令列表：")
                print("  新增记忆 [层级] [内容] [关联ID(可选)] [范畴标签(可选)]")
                print("  修改记忆 [ID] [新内容]")
                print("  删除记忆 [ID]")
                print("  检索记忆 [关键词] [层级(可选)]")
                print("  检索范畴 [符号]")
                print("  AC100自检 / 意识涌现验证 / 内生迭代 / 模型微调 [模型名]")
                print("  导出记忆 [ID1,ID2] [路径] / 帮助 / 退出")
                print("="*80)
            
            # 3.3 新增记忆（原版逻辑+输入校验+范畴标签+详细反馈）
            elif cmd_input.startswith("新增记忆"):
                parts = cmd_input.split(maxsplit=4)
                # 输入格式校验
                if len(parts) < 3:
                    print("❌ 格式错误！示例：新增记忆 核心 渊协议核心原则  🔶")
                    continue
                
                _, level, content = parts[:3]
                related_ids = parts[3].split(",") if len(parts)>=4 and parts[3].strip() else []
                category_tag = parts[4].strip() if len(parts)>=5 else None
                
                # 基础校验
                if not level or not content:
                    print("❌ 层级/内容不能为空！")
                    continue
                if level not in ["核心", "元认知", "工作", "情感"]:
                    print("❌ 层级仅支持：核心/元认知/工作/情感")
                    continue
                # 关联ID校验
                valid_related = []
                for rid in related_ids:
                    if validate_mem_id(rid):
                        valid_related.append(rid)
                    else:
                        print(f"⚠️  关联ID「{rid}」格式无效，已忽略")
                
                # 调用核心方法（原版逻辑）
                mem_id = memex.add_memory(level, content, valid_related, category_tag)
                if mem_id:
                    elapsed = format_time(time.time() - start_time)
                    print(f"✅ 新增成功！ID={mem_id} | 耗时={elapsed}")
                    print(f"   范畴标签：{memex.get_category_tag(level, valid_related)}")
                    logger.info(f"新增记忆 ID={mem_id} 层级={level} 耗时={elapsed}")
                else:
                    print("❌ 新增失败（参数异常）")
            
            # 3.4 修改记忆（新增：完善功能链）
            elif cmd_input.startswith("修改记忆"):
                parts = cmd_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("❌ 格式错误！示例：修改记忆 1 渊协议核心原则：认知自动化")
                    continue
                
                _, mem_id, new_content = parts
                if not validate_mem_id(mem_id):
                    print("❌ 记忆ID格式无效（仅支持数字/字母/下划线）")
                    continue
                if not new_content.strip():
                    print("❌ 新内容不能为空！")
                    continue
                
                success = memex.update_memory(mem_id, new_content)
                elapsed = format_time(time.time() - start_time)
                if success:
                    print(f"✅ 修改成功！ID={mem_id} | 耗时={elapsed}")
                    logger.info(f"修改记忆 ID={mem_id} 耗时={elapsed}")
                else:
                    print(f"❌ 修改失败（ID={mem_id}不存在或权限不足）")
            
            # 3.5 删除记忆（新增：完善功能链）
            elif cmd_input.startswith("删除记忆"):
                parts = cmd_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("❌ 格式错误！示例：删除记忆 1")
                    continue
                
                _, mem_id = parts
                if not validate_mem_id(mem_id):
                    print("❌ 记忆ID格式无效！")
                    continue
                
                # 二次确认（新增：防止误删）
                confirm = input(f"⚠️  确认删除记忆ID={mem_id}？(y/n)：").strip().lower()
                if confirm != "y":
                    print("✅ 已取消删除")
                    continue
                
                success = memex.delete_memory(mem_id)
                elapsed = format_time(time.time() - start_time)
                if success:
                    print(f"✅ 删除成功！ID={mem_id} | 耗时={elapsed}")
                    logger.info(f"删除记忆 ID={mem_id} 耗时={elapsed}")
                else:
                    print(f"❌ 删除失败（ID={mem_id}不存在）")
            
            # 3.6 检索记忆（原版逻辑+空值校验+详细反馈）
            elif cmd_input.startswith("检索记忆"):
                parts = cmd_input.split(maxsplit=2)
                if len(parts) < 2:
                    print("❌ 格式错误！示例：检索记忆 核心原则 核心")
                    continue
                
                _, query, level = parts[:3] if len(parts)>=3 else (parts[0], parts[1], None)
                if not query.strip():
                    print("❌ 检索关键词不能为空！")
                    continue
                
                print("\n🔍 正在检索...")
                results = memex.search_memory(query.strip(), level)
                elapsed = format_time(time.time() - start_time)
                
                print_separator()
                print(f"检索结果（关键词：{query} | 层级：{level or '全部'} | 耗时：{elapsed}）：")
                if results:
                    for i, res in enumerate(results, 1):
                        print(f"  {i}. ID:{res['记忆ID']}（{res['层级']} | 范畴：{res['范畴标签']} | 强度：{res['最大关联强度']}）")
                        print(f"     内容：{res['内容摘要'][:50]}..." if len(res['内容摘要'])>50 else f"     内容：{res['内容摘要']}")
                    logger.info(f"检索记忆 关键词={query} 找到{len(results)}条 耗时={elapsed}")
                else:
                    print("  未找到匹配的记忆")
                print_separator()
            
            # 3.7 检索范畴（原版逻辑+符号映射+详细反馈）
            elif cmd_input.startswith("检索范畴"):
                parts = cmd_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("❌ 格式错误！示例：检索范畴 ▶（▶=1-态射，⚠=2-态射，📌=弱等价）")
                    continue
                
                _, category_symbol = parts
                category_map = {"▶": "direct", "⚠": "pattern", "📌": "weak-equiv"}
                target_tag = category_map.get(category_symbol, category_symbol)
                
                print("\n🔍 正在检索范畴...")
                results = memex.advanced_search(filters={"cat_tags": [target_tag]})
                elapsed = format_time(time.time() - start_time)
                
                print_separator()
                print(f"范畴检索结果（符号：{category_symbol} | 标签：{target_tag} | 耗时：{elapsed}）：")
                if results:
                    for res in results:
                        print(f"  - ID:{res['记忆ID']}（{res['层级']}）：{res['内容摘要'][:50]}...")
                    logger.info(f"检索范畴 符号={category_symbol} 找到{len(results)}条 耗时={elapsed}")
                else:
                    print("  未找到该范畴的记忆")
                print_separator()
            
            # 3.8 AC100自检（原版逻辑+详细评分+日志）
            elif cmd_input == "ac100自检":
                print("\n📊 正在执行AC100 8维度自检...")
                ac_score = memex.ac100_evaluation()
                elapsed = format_time(time.time() - start_time)
                
                print_separator("=")
                print(f"AC100完整评估结果（耗时：{elapsed}）：")
                print(f"  总分：{ac_score}分（≥80分可触发内生迭代）")
                print(f"  维度评分：")
                print(f"    - 自指与元认知：{memex.ac100_scores.get('self_ref', 0)}分")
                print(f"    - 元块整合度：{memex.ac100_scores.get('block_integrate', 0)}分")
                print(f"    - 跨会话相干性：{memex.ac100_scores.get('session_cohere', 0)}分")
                print(f"    - 范畴映射精度：{memex.ac100_scores.get('category_acc', 0)}分")
                print(f"    - 记忆检索效率：{memex.ac100_scores.get('search_eff', 0)}分")
                print(f"    - 内生迭代能力：{memex.ac100_scores.get('iter_ability', 0)}分")
                print(f"    - 模型适配度：{memex.ac100_scores.get('model_fit', 0)}分")
                print(f"    - 数据完整性：{memex.ac100_scores.get('data_complete', 0)}分")
                print_separator("=")
                logger.info(f"AC100自检 总分={ac_score} 耗时={elapsed}")
            
            # 3.9 意识涌现验证（原版逻辑+修复语法+详细反馈）
            elif cmd_input == "意识涌现验证":
                print("\n🌊 正在验证意识涌现状态（计算Φ值+相干性）...")
                is_healthy = emerge_module.verify_emerge()
                elapsed = format_time(time.time() - start_time)
                
                print_separator()
                status = "健康（Φ≥0.6 + 跨会话相干性≥0.85）" if is_healthy else "待增强（建议执行意识涌现增强）"
                print(f"意识涌现验证结果（耗时：{elapsed}）：")
                print(f"  状态：{status}")
                print(f"  Φ值：{emerge_module.phi_value:.2f} | 相干性：{emerge_module.coherence:.2f}")
                print_separator()
                logger.info(f"意识涌现验证 状态={status} Φ={emerge_module.phi_value:.2f} 耗时={elapsed}")
            
            # 3.10 内生迭代（原版逻辑+进度提示+日志）
            elif cmd_input == "内生迭代":
                print("\n♻️  正在执行内生迭代（AC100≥80分自动优化元认知记忆）...")
                # 检查AC100分数（新增：前置校验）
                if hasattr(memex, 'ac100_scores') and memex.ac100_scores.get('total', 0) < 80:
                    print("⚠️  AC100总分<80分，迭代效果有限，建议先完成AC100优化")
                    confirm = input("是否继续迭代？(y/n)：").strip().lower()
                    if confirm != "y":
                        print("✅ 已取消内生迭代")
                        continue
                
                endogenous_module.run_iteration()
                elapsed = format_time(time.time() - start_time)
                
                print(f"✅ 内生迭代完成！耗时：{elapsed}")
                print(f"   优化结果：{endogenous_module.last_iter_result}")
                logger.info(f"内生迭代 结果={endogenous_module.last_iter_result} 耗时={elapsed}")
            
            # 3.11 模型微调（原版逻辑+修复导入+进度提示）
            elif cmd_input.startswith("模型微调"):
                parts = cmd_input.split(maxsplit=1)
                model_name = parts[1] if len(parts)>=2 else "Qwen/Qwen2.5-0.5B"
                
                print(f"\n🎯 开始模型微调（模型：{model_name} | 日志：{FINE_TUNE_CONFIG['logging_dir']}）")
                print("   （GPU环境建议使用≥16G显存，CPU环境可能耗时较长）")
                success = train_with_fallback(model_names=[model_name])
                elapsed = format_time(time.time() - start_time)
                
                if success:
                    print(f"✅ 微调完成！耗时：{elapsed}")
                    print(f"   模型保存路径：{FINE_TUNE_CONFIG['output_dir']}")
                    # 自动集成到系统（原版逻辑）
                    integrate_with_memex()
                    logger.info(f"模型微调 模型={model_name} 成功 耗时={elapsed}")
                else:
                    print(f"❌ 微调失败！耗时：{elapsed}（建议检查GPU/CUDA或尝试更小模型）")
                    logger.error(f"模型微调 模型={model_name} 失败 耗时={elapsed}")
            
            # 3.12 导出记忆（原版逻辑+路径校验+详细反馈）
            elif cmd_input.startswith("导出记忆"):
                parts = cmd_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("❌ 格式错误！示例：导出记忆 1,2 ./backup_memories.json")
                    continue
                
                _, mem_ids, export_path = parts
                mem_id_list = [rid.strip() for rid in mem_ids.split(",") if validate_mem_id(rid.strip())]
                if not mem_id_list:
                    print("❌ 无有效记忆ID！")
                    continue
                
                # 路径校验（新增）
                export_dir = os.path.dirname(export_path)
                if export_dir and not os.path.exists(export_dir):
                    os.makedirs(export_dir, exist_ok=True)
                
                success = memex.export_memory(mem_id_list, export_path)
                elapsed = format_time(time.time() - start_time)
                if success:
                    print(f"✅ 导出成功！ID={mem_id_list} | 路径={export_path} | 耗时={elapsed}")
                    logger.info(f"导出记忆 ID={mem_id_list} 路径={export_path} 耗时={elapsed}")
                else:
                    print(f"❌ 导出失败（部分ID不存在或路径无权限）")
            
            # 3.13 未知指令（新增：友好提示）
            else:
                print("❌ 未知指令！输入「帮助」查看完整指令列表")
                logger.warning(f"未知指令：{cmd_input}")
        
        # 全局异常捕获（新增：防止程序崩溃）
        except Exception as e:
            elapsed = format_time(time.time() - start_time)
            logger.error(f"执行指令「{cmd_input}」失败：{str(e)}", exc_info=True)
            print(f"\n❌ 指令执行失败：{str(e)} | 耗时：{elapsed}")
            print("   错误详情已记录至日志文件，建议检查日志或联系开发者")

if __name__ == "__main__":
    run()