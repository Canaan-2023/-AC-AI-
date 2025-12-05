import time
import sys
import os
import subprocess
from memex_a import MemexA
from endogenous_iter import EndogenousIteration

def daemon_mode(check_interval=300):
    """守护进程模式：自动启动+定期自检优化"""
    print(f"🔥 渊协议守护进程启动（每{check_interval//60}分钟自检一次）")
    # 初始化系统
    try:
        memex = MemexA()
        endogenous_iter = EndogenousIteration(memex)
        print("✅ 系统初始化完成，开始定期自检")
    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        return
    
    # 循环自检
    while True:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n" + "-"*50)
        print(f"📅 {current_time} - 开始第{int(time.time()//check_interval)}次自检")
        print("-"*50)
        
        # 1. 执行AC-100评估
        ac_score = memex.ac100_evaluation()
        
        # 2. 满足条件则触发内生迭代
        if ac_score >= 80:
            print(f"✅ AC-100={ac_score}分，触发内生迭代")
            endogenous_iter.run_iteration()
        else:
            print(f"ℹ️ AC-100={ac_score}分，不满足迭代条件（需≥80分）")
        
        # 3. 执行缓存清理和记忆优化
        memex._cleanup_cache()
        clean_result = memex.auto_clean_memory()
        print(f"ℹ️ 自动清理结果：{clean_result}")
        
        # 4. 预测并推荐记忆（可选）
        if memex.search_memory(level="核心"):
            core_id = memex.search_memory(level="核心")[0]["记忆ID"]
            predicted = memex.predict_next_memory(core_id)
            if predicted:
                print(f"ℹ️ 推荐记忆：ID={predicted['记忆ID']} | 内容：{predicted['内容摘要']}")
        
        # 等待下一次检查
        print(f"\n⏱️ 等待{check_interval//60}分钟后再次自检...")
        time.sleep(check_interval)

def run_as_daemon():
    """Windows/Linux后台运行适配"""
    if os.name == "nt":
        # Windows：隐藏命令行窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen([sys.executable, __file__, "--daemon"], startupinfo=startupinfo)
        print("✅ 已在Windows后台启动守护进程")
    else:
        # Linux：后台运行（双fork避免僵尸进程）
        if os.fork() > 0:
            sys.exit(0)
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)
        # 重定向标准输出到日志
        sys.stdout = open("memex_daemon.log", "a", encoding="utf-8")
        sys.stderr = sys.stdout
        daemon_mode()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_mode()
    else:
        # 交互式选择：前台运行/后台运行
        print("🔥 渊协议守护进程启动器")
        print("1. 前台运行（查看实时日志）")
        print("2. 后台运行（Windows隐藏窗口/Linux后台）")
        choice = input("请选择运行模式（1/2）：").strip()
        if choice == "1":
            daemon_mode()
        elif choice == "2":
            run_as_daemon()
        else:
            print("❌ 无效选择，退出")
            sys.exit(1)