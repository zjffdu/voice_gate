#!/usr/bin/env python3
"""
清理 audio_samples 目录中的重复音频文件
保留每个用户每个样本编号最早的文件，删除其他重复文件
"""

import os
import pickle
from collections import defaultdict

AUDIO_DIR = "audio_samples"
DB_PATH = "voice_db.pkl"

def cleanup_duplicates():
    """清理重复的音频文件"""
    
    # 加载数据库，获取每个用户应该有的样本
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            db = pickle.load(f)
    else:
        db = {}
    
    # 扫描所有音频文件
    files = sorted(os.listdir(AUDIO_DIR))
    
    # 按用户和样本编号分组
    grouped = defaultdict(list)
    
    for filename in files:
        if not filename.endswith('.wav'):
            continue
        
        # 解析文件名: user_id_sample_index_timestamp.wav
        parts = filename.rsplit('_', 2)
        if len(parts) >= 3:
            user_id = parts[0]
            sample_index = parts[1]
            key = (user_id, sample_index)
            grouped[key].append(filename)
    
    # 统计信息
    total_files = len(files)
    kept_files = 0
    deleted_files = 0
    
    print(f"📊 发现 {total_files} 个音频文件")
    print(f"📋 涉及 {len(grouped)} 个不同的用户-样本组合")
    print()
    
    # 对每个分组，保留最早的文件，删除其他
    for (user_id, sample_index), file_list in grouped.items():
        if len(file_list) > 1:
            # 按时间戳排序（文件名中包含时间戳）
            file_list.sort()
            
            # 保留第一个（最早的）
            kept_file = file_list[0]
            duplicates = file_list[1:]
            
            print(f"👤 {user_id} - 样本 {sample_index}:")
            print(f"   ✅ 保留: {kept_file}")
            print(f"   ❌ 删除: {len(duplicates)} 个重复文件")
            
            # 删除重复文件
            for dup_file in duplicates:
                filepath = os.path.join(AUDIO_DIR, dup_file)
                os.remove(filepath)
                deleted_files += 1
                print(f"      - {dup_file}")
            
            kept_files += 1
            print()
        else:
            kept_files += 1
    
    print("=" * 60)
    print(f"✅ 清理完成！")
    print(f"📝 保留文件: {kept_files}")
    print(f"🗑️  删除文件: {deleted_files}")
    print(f"💾 剩余文件: {kept_files}")

if __name__ == "__main__":
    cleanup_duplicates()
