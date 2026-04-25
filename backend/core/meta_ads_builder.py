from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from .meta_client import init_meta_api
import structlog

logger = structlog.get_logger()

OBJECTIVE_BILLING_MAP = {
    "OUTCOME_LEADS": "IMPRESSIONS",
    "OUTCOME_TRAFFIC": "IMPRESSIONS",
    "OUTCOME_SALES": "IMPRESSIONS",
    "OUTCOME_AWARENESS": "IMPRESSIONS",
    "OUTCOME_ENGAGEMENT": "IMPRESSIONS",
}

CTA_MAP = {
    "LEARN_MORE": "LEARN_MORE",
    "SIGN_UP": "SIGN_UP",
    "SHOP_NOW": "SHOP_NOW",
    "CONTACT_US": "CONTACT_US",
    "GET_QUOTE": "GET_QUOTE",
    "BOOK_TRAVEL": "BOOK_TRAVEL",
    "Saiba Mais": "LEARN_MORE",
    "Cadastre-se": "SIGN_UP",
    "Comprar Agora": "SHOP_NOW",
    "Fale Conosco": "CONTACT_US",
    "Solicitar Orçamento": "GET_QUOTE",
}


def create_ad_set(
    ad_account_id: str,
    campaign_id: str,
    name: str,
    daily_budget_cents: int,
    targeting: dict,
    campaign_objective: str = "OUTCOME_LEADS",
    status: str = "PAUSED",
) -> dict:
    init_meta_api()
    logger.info("creating_ad_set", campaign_id=campaign_id, name=name)

    account = AdAccount(ad_account_id)
    ad_set = account.create_ad_set(
        fields=[AdSet.Field.id, AdSet.Field.name],
        params={
            AdSet.Field.name: name,
            AdSet.Field.campaign_id: campaign_id,
            AdSet.Field.daily_budget: daily_budget_cents,
            AdSet.Field.billing_event: "IMPRESSIONS",
            AdSet.Field.optimization_goal: _get_optimization_goal(campaign_objective),
            AdSet.Field.targeting: targeting,
            AdSet.Field.status: status,
        },
    )
    return {"id": ad_set["id"], "name": name, "status": status}


def upload_image(ad_account_id: str, image_path: str) -> dict:
    init_meta_api()
    logger.info("uploading_image", account=ad_account_id)
    account = AdAccount(ad_account_id)
    img = account.create_ad_image(
        params={"filename": image_path},
        files={"filename": open(image_path, "rb")},
    )
    return {"hash": img["images"][image_path.split("/")[-1]]["hash"]}


def create_ad_creative(
    ad_account_id: str,
    name: str,
    page_id: str,
    image_hash: str,
    primary_text: str,
    headline: str,
    description: str,
    cta_type: str,
    link_url: str,
) -> dict:
    init_meta_api()
    logger.info("creating_ad_creative", name=name)

    account = AdAccount(ad_account_id)
    creative = account.create_ad_creative(
        fields=[AdCreative.Field.id],
        params={
            AdCreative.Field.name: name,
            AdCreative.Field.object_story_spec: {
                "page_id": page_id,
                "link_data": {
                    "image_hash": image_hash,
                    "link": link_url,
                    "message": primary_text,
                    "name": headline,
                    "description": description,
                    "call_to_action": {
                        "type": CTA_MAP.get(cta_type, "LEARN_MORE"),
                        "value": {"link": link_url},
                    },
                },
            },
        },
    )
    return {"id": creative["id"], "name": name}


def create_ad(
    ad_account_id: str,
    name: str,
    ad_set_id: str,
    creative_id: str,
    status: str = "PAUSED",
) -> dict:
    init_meta_api()
    logger.info("creating_ad", name=name, ad_set_id=ad_set_id)

    account = AdAccount(ad_account_id)
    ad = account.create_ad(
        fields=[Ad.Field.id, Ad.Field.name],
        params={
            Ad.Field.name: name,
            Ad.Field.adset_id: ad_set_id,
            Ad.Field.creative: {"creative_id": creative_id},
            Ad.Field.status: status,
        },
    )
    return {"id": ad["id"], "name": name, "status": status}


def _get_optimization_goal(objective: str) -> str:
    goals = {
        "OUTCOME_LEADS": "LEAD_GENERATION",
        "OUTCOME_TRAFFIC": "LINK_CLICKS",
        "OUTCOME_SALES": "OFFSITE_CONVERSIONS",
        "OUTCOME_AWARENESS": "REACH",
        "OUTCOME_ENGAGEMENT": "POST_ENGAGEMENT",
    }
    return goals.get(objective, "LEAD_GENERATION")


def build_targeting(
    age_min: int = 18,
    age_max: int = 65,
    genders: list = None,
    geo_locations: dict = None,
    interests: list = None,
) -> dict:
    targeting = {
        "age_min": age_min,
        "age_max": age_max,
    }
    if genders:
        targeting["genders"] = genders  # 1=male, 2=female
    if geo_locations:
        targeting["geo_locations"] = geo_locations
    else:
        targeting["geo_locations"] = {"countries": ["BR"]}
    if interests:
        targeting["flexible_spec"] = [{"interests": interests}]
    return targeting
