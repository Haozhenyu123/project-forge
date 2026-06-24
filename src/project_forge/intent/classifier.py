"""Keyword-based intent classifier with domain profile loading.

First pass uses deterministic keyword matching for zero latency.
Second pass (optional) delegates to LLM when confidence is below threshold.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import DomainProfile, IntentResult


DOMAINS_DIR = Path(__file__).resolve().parent / "domains"

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "medical": [
        "medical", "clinic", "hospital", "patient", "diagnosis", "treatment",
        "health", "doctor", "nurse", "pharmacy", "drug", "prescription",
        "symptom", "disease", "therapy", "surgery", "ehr", "emr",
        "telemedicine", "healthcare", "clinical", "radiology",
        "medical record", "hippa", "fda", "medical device", "medical imaging",
        "医疗", "医院", "看病", "问诊",
        "诊断", "患者", "症状", "药",
        "处方", "门诊", "中医", "西医",
        "体检", "挂号", "就诊", "病历", "健康", "健身"
    ],
    "finance": [
        "finance", "bank", "trading", "investment", "stock", "crypto",
        "payment", "loan", "mortgage", "insurance", "tax", "accounting",
        "ledger", "audit", "wealth", "portfolio", "fintech",
        "credit", "debit", "payroll", "invoice", "billing",
        "金融", "银行", "交易", "投资",
        "股票", "支付", "贷款", "保险",
        "税务", "会计", "财务", "理财",
        "证券", "基金", "汇率", "钱包"
    ],
    "legal": [
        "legal", "law", "attorney", "contract", "court", "litigation",
        "compliance", "regulation", "ip", "patent", "trademark", "gdpr",
        "privacy law", "terms of service", "nda", "liability", "jurisdiction",
        "法律", "律师", "合同", "诉讼",
        "法规", "知识产权", "隐私",
        "条款", "仲裁", "判决", "公证"
    ],
    "education": [
        "education", "learning", "course", "student", "teacher", "classroom",
        "curriculum", "quiz", "exam", "training", "tutorial", "academy",
        "e-learning", "lms", "homework", "grade", "certification",
        "教育", "学习", "课程", "学生",
        "老师", "教室", "考试",
        "培训", "辅导", "作业", "学院",
        "大学", "网课", "题库"
    ],
    "gaming": [
        "game", "gaming", "player", "level", "score", "multiplayer",
        "3d game", "2d game", "rpg", "fps", "puzzle", "platformer",
        "shooter", "strategy game", "simulation", "arcade", "vr game",
        "unity", "unreal", "godot", "game engine",
        "游戏", "玩家", "关卡", "得分",
        "多人", "角色扮演",
        "射击", "益智", "模拟", "电竞",
        "手游", "页游", "卡牌", "对战"
    ],
    "ecommerce": [
        "ecommerce", "shop", "store", "cart", "checkout", "product",
        "inventory", "order", "shipping", "marketplace", "catalog",
        "retail", "wholesale", "pos", "merchant", "coupon", "discount",
        "电商", "商城", "购物", "店铺",
        "商品", "订单", "库存",
        "物流", "促销", "秒杀", "团购",
        "比价", "买家", "卖家", "点餐", "外卖", "商家"
    ],
    "enterprise": [
        "enterprise", "crm", "erp", "hr", "workflow", "bpm", "sso",
        "ldap", "saml", "sla", "on-premise", "self-hosted", "rbac",
        "internal tool", "admin panel",
        "企业", "办公", "oa", "审批",
        "考勤", "人事", "客户管理",
        "后台管理", "工单", "流程", "报销", "打卡"
    ],
    "content": [
        "content", "cms", "blog", "article", "media", "publishing",
        "news", "magazine", "podcast", "video", "streaming", "authoring",
        "editorial", "seo", "marketing", "landing page", "newsletter",
        "内容", "文章", "博客", "发布",
        "媒体", "编辑", "写作",
        "新闻", "视频", "直播", "文案"
    ],
    "iot": [
        "iot", "sensor", "embedded", "firmware", "microcontroller",
        "arduino", "raspberry pi", "mqtt", "ble", "zigbee", "edge",
        "smart home", "wearable", "actuator", "telemetry",
        "物联网", "传感器", "嵌入式",
        "智能家居", "可穿戴", "温控"
    ],
}

PRODUCT_FORM_KEYWORDS: Dict[str, List[str]] = {
    "mini-program": [
        "mini program", "miniprogram", "wechat app",
        "小程序", "微信小程序",
        "uni-app", "taro", "mpvue"
    ],
    "mobile-app": [
        "mobile app", "ios", "android", "react native", "flutter",
        "swift", "kotlin", "app store", "mobile",
        "手机", "移动", "app", "安卓",
        "跨平台"
    ],
    "desktop-app": [
        "desktop", "electron", "tauri", "wpf", "qt", "gtk",
        "native app", "offline app",
        "桌面", "客户端", "本地程序"
    ],
    "cli-tool": [
        "cli", "command line", "terminal tool", "bash",
        "automation tool", "dev tool",
        "命令行", "脚本工具", "自动化"
    ],
    "browser-extension": [
        "browser extension", "chrome extension", "firefox addon",
        "浏览器插件", "浏览器扩展"
    ],
    "api-service": [
        "api", "rest api", "graphql", "microservice", "backend",
        "webhook", "grpc",
        "后端", "接口", "服务"
    ],
    "game": [
        "game", "gaming", "3d game", "2d game", "unity", "unreal", "godot",
        "游戏", "手游", "页游", "卡牌", "对战"
    ],
    "embedded": [
        "embedded", "firmware", "microcontroller", "arduino",
        "raspberry pi", "iot",
        "嵌入式", "单片机"
    ],
}

TECH_FEATURE_KEYWORDS: Dict[str, List[str]] = {
    "real-time": [
        "real-time", "realtime", "websocket", "live", "streaming",
        "collaboration", "sync",
        "即时", "实时", "同步", "协作", "直播"
    ],
    "offline-first": [
        "offline", "local-first", "pwa", "offline mode",
        "no internet", "disconnected",
        "离线", "无网络", "本地优先"
    ],
    "ai-ml": [
        "ai", "ml", "machine learning", "deep learning", "neural",
        "llm", "gpt", "nlp", "computer vision", "rag", "embedding",
        "vector db", "transformer", "fine-tune", "graph rag",
        "人工智能", "机器学习",
        "深度学习", "模型", "大模型",
        "知识图谱", "语义", "向量"
    ],
    "data-heavy": [
        "big data", "analytics", "data warehouse", "etl", "pipeline",
        "hadoop", "spark", "dashboard", "reporting", "visualization",
        "大数据", "分析", "数据仓库",
        "报表", "图表", "可视化"
    ],
    "high-security": [
        "security", "encryption", "pii", "hipaa", "gdpr", "compliance",
        "audit trail", "authentication",
        "零信任", "安全", "加密", "合规",
        "审计", "权限"
    ],
    "low-latency": [
        "low latency", "high performance", "real-time", "edge",
        "c++", "rust",
        "低延迟", "高性能", "边缘计算"
    ],
    "collaboration": [
        "multi-user", "team", "collaboration", "shared", "workspace",
        "comment", "review",
        "多用户", "团队", "协作", "共享", "评论"
    ],
}


def _score_keywords(text, keyword_map):
    text_lower = text.lower()
    scores = {}
    for category, keywords in keyword_map.items():
        score = 0.0
        matched = 0
        for kw in keywords:
            if kw in text_lower:
                weight = 2.0 if len(kw) >= 4 else 1.0
                score += weight
                matched += 1
        if matched > 0:
            scores[category] = round(min(score / max(2.0, len(keywords) * 0.2), 1.0), 4)
    return scores


def _normalize_scores(scores):
    if not scores:
        return {}
    total = sum(scores.values())
    if total <= 0:
        return {}
    return {k: round(v / total, 4) for k, v in sorted(scores.items(), key=lambda x: -x[1])}


def _primary(scores):
    if not scores:
        return ("general", 1.0)
    best = max(scores.items(), key=lambda x: x[1])
    return (best[0], best[1])


def _load_domain_profile(domain):
    config_path = DOMAINS_DIR / f"{domain}.json"
    if not config_path.is_file():
        return None
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return DomainProfile.from_dict(data)
    except (OSError, ValueError, KeyError):
        return None


def classify_intent(goal, constraints=None, llm_fallback=False):

    full_text = goal
    if constraints:
        full_text += " " + " ".join(constraints)

    domain_scores = _score_keywords(full_text, DOMAIN_KEYWORDS)
    normalized_domains = _normalize_scores(domain_scores)
    primary_domain, confidence = _primary(normalized_domains)

    form_scores = _score_keywords(full_text, PRODUCT_FORM_KEYWORDS)
    product_form, form_conf = _primary(form_scores) if form_scores else ("web-app", 0.0)

    feature_scores = _score_keywords(full_text, TECH_FEATURE_KEYWORDS)
    features = sorted(feature_scores.keys(), key=lambda k: -feature_scores[k])

    profile = _load_domain_profile(primary_domain)
    if profile and profile.probing_axes:
        questions = [ax["prompt"] for ax in profile.probing_axes]
    else:
        questions = [
            "Who is the primary user and what is their core workflow?",
            "What platform or deployment target do you have in mind?",
            "What is the smallest useful version you could verify in a week?",
        ]

    return IntentResult(
        primary_domain=primary_domain,
        domain_confidence=confidence,
        all_domains=normalized_domains,
        product_form=product_form,
        product_form_confidence=form_conf,
        technical_features=features,
        recommended_questions=questions,
        domain_profile=profile,
    )
