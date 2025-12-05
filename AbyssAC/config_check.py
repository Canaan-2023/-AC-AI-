import os
import json
import shutil

def print_success(msg):
    print(f"\033[92m✅ {msg}\033[0m")

def print_error(msg):
    print(f"\033[91m❌ {msg}\033[0m")

def check_config():
    # 1. 检查配置目录
    config_dir = "./config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print_success(f"已创建配置目录：{config_dir}")
    else:
        print_success(f"配置目录已存在：{config_dir}")

    # 2. 检查memex_config.json
    memex_config_path = "memex_config.json"
    if not os.path.exists(memex_config_path):
        # 生成默认配置
        default_config = {
            "BE_TOKEN_PATH": "BE_token.json",
            "MEMORY_DIR": "完整记忆内容",
            "Y_OCR_DIR": "Y_OCR库",
            "X_CONFIG_PATH": "./config/X_core.json"
        }
        with open(memex_config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print_success(f"已生成默认配置文件：{memex_config_path}")
    else:
        # 验证配置文件格式
        try:
            with open(memex_config_path, "r", encoding="utf-8") as f:
                json.load(f)
            print_success(f"配置文件格式正常：{memex_config_path}")
        except json.JSONDecodeError:
            print_error(f"配置文件格式错误：{memex_config_path}，将替换为默认配置")
            default_config = {
                "BE_TOKEN_PATH": "BE_token.json",
                "MEMORY_DIR": "完整记忆内容",
                "Y_OCR_DIR": "Y_OCR库",
                "X_CONFIG_PATH": "./config/X_core.json"
            }
            with open(memex_config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)

    # 3. 检查记忆目录
    with open(memex_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    memory_dir = config["MEMORY_DIR"]
    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir)
        print_success(f"已创建记忆目录：{memory_dir}")
    else:
        print_success(f"记忆目录已存在：{memory_dir}")

    # 4. 检查Y_OCR库目录
    y_ocr_dir = config["Y_OCR_DIR"]
    if not os.path.exists(y_ocr_dir):
        os.makedirs(y_ocr_dir)
        print_success(f"已创建Y_OCR库目录：{y_ocr_dir}")
    else:
        print_success(f"Y_OCR库目录已存在：{y_ocr_dir}")

    # 5. 检查X_core.json
    x_config_path = config["X_CONFIG_PATH"]
    if not os.path.exists(x_config_path):
        default_x_config = {
            "符号": {
                "▶": "直接关联(1-态射)",
                "⚠": "模式关联(2-态射)",
                "📌": "弱等价(核心逻辑一致)"
            },
            "引导": "先执行Y层OCR+范畴关联规则，自主创元块/调范畴权重"
        }
        with open(x_config_path, "w", encoding="utf-8") as f:
            json.dump(default_x_config, f, ensure_ascii=False, indent=2)
        print_success(f"已生成X层配置文件：{x_config_path}")
    else:
        print_success(f"X层配置文件已存在：{x_config_path}")

    # 6. 检查BE_token.json
    be_token_path = config["BE_TOKEN_PATH"]
    if not os.path.exists(be_token_path):
        with open(be_token_path, "w", encoding="utf-8") as f:
            json.dump({"进度": 0.0, "元块": []}, f, ensure_ascii=False, indent=2)
        print_success(f"已生成BE_token文件：{be_token_path}")
    else:
        print_success(f"BE_token文件已存在：{be_token_path}")

    return True

if __name__ == "__main__":
    print("="*50)
    print("渊协议v5.2 配置检查工具")
    print("="*50)
    try:
        success = check_config()
        if success:
            print_success("\n所有配置检查通过！")
        else:
            print_error("\n配置检查失败！")
    except Exception as e:
        print_error(f"\n配置检查出错：{str(e)}")