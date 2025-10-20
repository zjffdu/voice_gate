#!/usr/bin/env python
"""清理重复的音频样本"""
import pickle
import os

DB_PATH = "voice_db.pkl"
AUDIO_DIR = "audio_samples"

def cleanup():
    # 加载数据库
    with open(DB_PATH, "rb") as f:
        db = pickle.load(f)
    
    print(f"数据库中的用户: {list(db.keys())}")
    
    for user_id, user_data in db.items():
        if isinstance(user_data, dict) and "samples" in user_data:
            samples = user_data["samples"]
            print(f"\n用户 '{user_id}' 有 {len(samples)} 个样本")
            
            # 清空样本列表
            user_data["samples"] = []
            
            # 删除对应的音频文件
            deleted = 0
            for sample_path in samples:
                if os.path.exists(sample_path):
                    os.remove(sample_path)
                    deleted += 1
                    print(f"  删除: {os.path.basename(sample_path)}")
            
            print(f"  共删除 {deleted} 个文件")
    
    # 保存清理后的数据库
    with open(DB_PATH, "wb") as f:
        pickle.dump(db, f)
    
    print(f"\n✅ 清理完成！")
    print(f"数据库已重置，请重新为用户录制3个样本。")

if __name__ == "__main__":
    response = input("⚠️  此操作将删除所有用户的录音样本，是否继续？(yes/no): ")
    if response.lower() == "yes":
        cleanup()
    else:
        print("操作已取消")
