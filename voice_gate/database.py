"""数据库管理"""

import os
import pickle
import numpy as np
from datetime import datetime
from voice_gate.config import DB_PATH


def load_db():
    """
    加载用户数据库
    
    Returns:
        dict: 用户数据库
    """
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            db = pickle.load(f)
            
            # 兼容旧版数据库（如果是旧格式，转换为新格式）
            if db and isinstance(list(db.values())[0], np.ndarray):
                # 旧格式：{user_id: embedding}
                # 转换为新格式：{user_id: {"embedding": embedding, "samples": []}}
                new_db = {}
                for user_id, embedding in db.items():
                    new_db[user_id] = {
                        "embedding": embedding,
                        "samples": [],
                        "created_at": datetime.now().isoformat()
                    }
                return new_db
            return db
    return {}


def save_db(db):
    """
    保存用户数据库
    
    Args:
        db: 用户数据库字典
    """
    with open(DB_PATH, "wb") as f:
        pickle.dump(db, f)


def create_user(user_id, prototype_embedding, audio_files):
    """
    创建新用户记录
    
    Args:
        user_id: 用户ID
        prototype_embedding: 原型向量
        audio_files: 音频文件路径列表
    
    Returns:
        dict: 用户数据字典
    """
    return {
        "embedding": prototype_embedding,
        "samples": audio_files.copy(),
        "created_at": datetime.now().isoformat()
    }


def delete_user(db, user_id):
    """
    删除用户及其音频文件
    
    Args:
        db: 数据库字典
        user_id: 要删除的用户ID
    
    Returns:
        bool: 是否成功删除
    """
    if user_id not in db:
        return False
    
    user_data = db[user_id]
    
    # 删除音频文件
    if isinstance(user_data, dict) and "samples" in user_data:
        for audio_path in user_data["samples"]:
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    # 删除数据库记录
    del db[user_id]
    save_db(db)
    return True


def delete_user_sample(db, user_id, sample_path):
    """
    删除用户的某个音频样本
    
    Args:
        db: 数据库字典
        user_id: 用户ID
        sample_path: 要删除的样本路径
    
    Returns:
        bool: 是否成功删除
    """
    if user_id not in db:
        return False
    
    user_data = db[user_id]
    
    if sample_path in user_data["samples"]:
        # 删除文件
        if os.path.exists(sample_path):
            os.remove(sample_path)
        
        # 从数据库移除
        user_data["samples"].remove(sample_path)
        save_db(db)
        return True
    
    return False


def add_user_sample(db, user_id, sample_path, new_embedding):
    """
    为用户添加新样本并更新原型向量
    
    Args:
        db: 数据库字典
        user_id: 用户ID
        sample_path: 新样本路径
        new_embedding: 新样本的embedding
    """
    if user_id not in db:
        return False
    
    user_data = db[user_id]
    
    # 添加样本
    user_data["samples"].append(sample_path)
    
    # 重新计算原型向量（需要重新提取所有样本的特征）
    # 这个由调用方处理，这里只更新embedding
    user_data["embedding"] = new_embedding
    
    save_db(db)
    return True


def get_user_stats(db):
    """
    获取数据库统计信息
    
    Args:
        db: 数据库字典
    
    Returns:
        dict: 统计信息
    """
    total_users = len(db)
    total_samples = sum(
        len(user_data.get("samples", [])) 
        if isinstance(user_data, dict) else 0 
        for user_data in db.values()
    )
    avg_samples = total_samples / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "total_samples": total_samples,
        "avg_samples": avg_samples
    }
