"""声纹验证功能"""

import numpy as np
from scipy.spatial.distance import cdist


def verify_voice(probe_embedding, db, threshold=0.75):
    """
    进行声纹验证
    
    Args:
        probe_embedding: 待验证的声纹特征
        db: 用户数据库
        threshold: 验证阈值
    
    Returns:
        dict: 验证结果，包含：
            - matched_user: 匹配的用户ID
            - similarity: 相似度
            - passed: 是否通过验证
            - all_similarities: 所有用户的相似度字典
    """
    if not db:
        return None
    
    # 重塑为二维数组
    probe = probe_embedding.reshape(1, -1)
    
    # 与数据库中所有用户比较
    keys = list(db.keys())
    mats = np.stack([
        db[k]["embedding"] if isinstance(db[k], dict) else db[k] 
        for k in keys
    ], axis=0)
    
    # 计算余弦相似度
    sims = 1 - cdist(probe, mats, metric="cosine")[0]
    
    # 找到最匹配的用户
    best_i = np.argmax(sims)
    matched_user = keys[best_i]
    similarity = sims[best_i]
    
    # 创建所有相似度字典
    all_similarities = {keys[i]: sims[i] for i in range(len(keys))}
    
    return {
        "matched_user": matched_user,
        "similarity": float(similarity),
        "passed": similarity >= threshold,
        "all_similarities": all_similarities,
        "threshold": threshold
    }


def get_similarity_ranking(all_similarities, threshold):
    """
    获取相似度排名
    
    Args:
        all_similarities: 所有用户的相似度字典
        threshold: 验证阈值
    
    Returns:
        list: 排名列表，每项包含 (rank, user_id, similarity, passed)
    """
    # 按相似度降序排序
    sorted_items = sorted(
        all_similarities.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    ranking = []
    for rank, (user_id, similarity) in enumerate(sorted_items, 1):
        ranking.append({
            "rank": rank,
            "user_id": user_id,
            "similarity": similarity,
            "passed": similarity >= threshold
        })
    
    return ranking
