#!/usr/bin/env python3
"""
测试模块化结构
"""

def test_imports():
    """测试所有模块是否可以正确导入"""
    print("🧪 测试模块导入...")
    
    try:
        from voice_gate import config
        print("✅ config模块导入成功")
        
        from voice_gate import audio_processor
        print("✅ audio_processor模块导入成功")
        
        from voice_gate import database
        print("✅ database模块导入成功")
        
        from voice_gate import verifier
        print("✅ verifier模块导入成功")
        
        from voice_gate import ui_styles
        print("✅ ui_styles模块导入成功")
        
        from voice_gate.ui import sidebar
        print("✅ sidebar组件导入成功")
        
        from voice_gate.ui import enrollment_page
        print("✅ enrollment_page组件导入成功")
        
        from voice_gate.ui import verification_page
        print("✅ verification_page组件导入成功")
        
        from voice_gate.ui import database_page
        print("✅ database_page组件导入成功")
        
        print("\n✅ 所有模块导入测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块导入失败: {e}")
        return False


def test_config():
    """测试配置模块"""
    print("\n🧪 测试配置模块...")
    
    try:
        from voice_gate.config import (
            DB_PATH, AUDIO_DIR, MODEL_SAMPLE_RATE,
            EMBEDDING_DIM, ENROLLMENT_SAMPLES_COUNT, DEFAULT_THRESHOLD
        )
        
        assert DB_PATH == "voice_db.pkl", "DB_PATH配置错误"
        assert AUDIO_DIR == "audio_samples", "AUDIO_DIR配置错误"
        assert MODEL_SAMPLE_RATE == 16000, "MODEL_SAMPLE_RATE配置错误"
        assert EMBEDDING_DIM == 256, "EMBEDDING_DIM配置错误"
        assert ENROLLMENT_SAMPLES_COUNT == 3, "ENROLLMENT_SAMPLES_COUNT配置错误"
        assert DEFAULT_THRESHOLD == 0.75, "DEFAULT_THRESHOLD配置错误"
        
        print("✅ 配置模块测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        return False


def test_database_functions():
    """测试数据库函数"""
    print("\n🧪 测试数据库函数...")
    
    try:
        from voice_gate.database import load_db, get_user_stats
        
        # 测试加载数据库
        db = load_db()
        print(f"  数据库加载成功，用户数: {len(db)}")
        
        # 测试统计功能
        stats = get_user_stats(db)
        print(f"  统计信息: {stats}")
        
        assert "total_users" in stats, "统计信息缺少total_users"
        assert "total_samples" in stats, "统计信息缺少total_samples"
        assert "avg_samples" in stats, "统计信息缺少avg_samples"
        
        print("✅ 数据库功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库功能测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Voice Gate 模块化结构测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("配置模块", test_config()))
    results.append(("数据库功能", test_database_functions()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！模块化结构运行正常。")
        print("💡 可以使用 'uv run streamlit run app.py' 启动应用")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    print("=" * 60)


if __name__ == "__main__":
    main()
