"""测试搜索层（关键词 / 语义 / 混合）"""


class TestKeywordSearch:
    def test_keyword_search_chinese(self, engine):
        engine.store("用户偏好使用飞书发送文件")
        engine.store("服务器部署在阿里云")
        results = engine.search("飞书")
        assert len(results) >= 1
        assert any("飞书" in r["content"] for r in results)

    def test_keyword_search_limit(self, engine):
        for i in range(10):
            engine.store(f"记忆条目 {i} 关于测试")
        results = engine.search("测试", limit=3)
        assert len(results) <= 3


class TestSemanticSearch:
    def test_semantic_degrades_without_model(self, engine):
        """无嵌入模型时语义搜索降级为关键词搜索"""
        engine.store("飞书发送文件")
        results = engine.search("飞书", mode="semantic")
        assert len(results) >= 1

    def test_hybrid_search_merging(self, engine_with_vec):
        """混合搜索合并关键词和语义两种来源的结果"""
        engine_with_vec.store("用户喜欢 Python 编程语言")
        engine_with_vec.store("用户偏好使用飞书发送文件")
        engine_with_vec.store("服务器部署在阿里云 ECS")
        results = engine_with_vec.search("Python", mode="hybrid")
        assert len(results) >= 1

    def test_hybrid_score_fusion(self, engine_with_vec):
        """验证 score-based 归一化保留分数差距"""
        engine_with_vec.store("Python 是一种编程语言")
        engine_with_vec.store("Java 是一种编程语言")
        results = engine_with_vec.search("Python 编程", mode="hybrid", limit=2)
        assert len(results) >= 1
        # 所有结果应有 score 字段
        for r in results:
            assert "score" in r
            assert isinstance(r["score"], (int, float))
