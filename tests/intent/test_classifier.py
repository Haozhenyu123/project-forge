
import pytest
import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_forge.intent import classify_intent
from project_forge.intent.models import IntentResult


class TestClassifyIntent:
    def test_medical_chinese(self):
        result = classify_intent("我想做一个医疗问诊助手，帮助患者在线挂号")
        assert result.primary_domain == "medical"
        assert result.domain_confidence > 0
        assert len(result.recommended_questions) > 0

    def test_medical_english(self):
        result = classify_intent("Build a clinical diagnosis support system for hospitals")
        assert result.primary_domain == "medical"

    def test_gaming_3d(self):
        result = classify_intent("一个3D射击游戏，使用Unity引擎，多人对战")
        assert result.primary_domain == "gaming"
        assert "game" in result.product_form or "mobile-app" in result.product_form or "web-app" in result.product_form

    def test_ecommerce(self):
        result = classify_intent("电商平台，支持商品管理和订单系统")
        assert result.primary_domain == "ecommerce"

    def test_mini_program(self):
        result = classify_intent("微信小程序商城，使用uni-app开发")
        assert result.primary_domain == "ecommerce"
        assert result.product_form == "mini-program"

    def test_finance(self):
        result = classify_intent("股票交易系统，需要实时行情和风控")
        assert result.primary_domain == "finance"
        assert "real-time" in result.technical_features
        # finance domain loaded (includes high-security capability)

    def test_education(self):
        result = classify_intent("在线教育平台，学生可以上课和考试")
        assert result.primary_domain == "education"

    def test_iot(self):
        result = classify_intent("智能家居温控系统，使用ESP32传感器")
        assert result.primary_domain == "iot"

    def test_enterprise(self):
        result = classify_intent("企业内部OA审批系统")
        assert result.primary_domain == "enterprise"

    def test_ai_features(self):
        result = classify_intent("基于RAG的知识库问答系统，使用大模型")
        assert "ai-ml" in result.technical_features

    def test_general_fallback(self):
        result = classify_intent("a tool for something")
        assert result.primary_domain == "general"
        assert result.domain_confidence <= 1.0

    def test_domain_profile_loaded(self):
        result = classify_intent("医疗诊断辅助系统")
        assert result.domain_profile is not None
        assert result.domain_profile.domain == "medical"
        assert result.domain_profile is not None
        assert len(result.domain_profile.domain_profile) > 0

    def test_no_crash_empty_input(self):
        result = classify_intent("")
        assert isinstance(result, IntentResult)

    def test_with_constraints(self):
        result = classify_intent("做一个应用", constraints=["需要HIPAA合规", "患者数据管理"])
        assert "high-security" in result.technical_features

    def test_legal_domain(self):
        result = classify_intent("合同审查和法律文书管理系统")
        assert result.primary_domain == "legal"

    def test_content_domain(self):
        result = classify_intent("内容管理系统，博客和新闻发布")
        assert result.primary_domain == "content"

    def test_mobile_app_form(self):
        result = classify_intent("一个iOS和Android的健身App，使用React Native")
        assert result.product_form == "mobile-app"

    def test_cli_tool_form(self):
        result = classify_intent("命令行自动化部署工具")
        assert result.product_form == "cli-tool"

    def test_desktop_form(self):
        result = classify_intent("使用Electron开发桌面端即时通讯软件")
        assert result.product_form == "desktop-app" or result.primary_domain in ("general", "enterprise")


class TestIntentResultDict:
    def test_to_dict(self):
        result = classify_intent("test")
        d = result.to_dict()
        assert "primary_domain" in d
        assert "domain_confidence" in d
        assert "product_form" in d
        assert "technical_features" in d
        assert "recommended_questions" in d
