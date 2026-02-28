

class TestAppHandler:

    def test_completions(self, client):
        """测试 completions 接口"""
        print(111)
        resp = client.post("/app/completion", json={"query": "你好"})
        print(resp.json)
        assert resp.status_code == 200
        assert resp.json["code"] == "success"

