from typing import Literal, Optional
from pydantic import BaseModel, Field


class Link(BaseModel):
    iOS: Optional[str] = None
    android: Optional[str] = None
    web: Optional[str] = None


class BannerContent(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    actionType: Literal["default", "externalLink", "openSmartLink",
                        "closeCampaign", "doneCampaign"]
    link: Optional[Link] = None
    buttonName: Optional[str] = None
    voiceOver: Optional[str] = Field(default=None, max_length=200)


class PromoText(BaseModel):
    role: Literal["text"]
    format: Literal["none", "html"]
    text: str


class PromoImage(BaseModel):
    role: Literal["image"]
    url: str


class PromoButton(BaseModel):
    role: Literal["button"]
    text: str
    actionType: Literal["default", "externalLink", "openSmartLink",
                        "closeCampaign", "doneCampaign"]
    link: Optional[Link] = None


class LinearContainer(BaseModel):
    role: Literal["linearContainer"]
    axis: Literal["v"] = "v"
    components: list[PromoText | PromoImage | PromoButton] = Field(
        min_length=1, max_length=6
    )


class PromoContent(BaseModel):
    role: Literal["promo"]
    component: LinearContainer


class CampaignDraft(BaseModel):
    """Черновик, который агент собирает в state (§2.2)."""
    name: Optional[str] = None
    marketingName: Optional[str] = None
    startDate: Optional[str] = None
    startTime: Optional[str] = None
    endDate: Optional[str] = None
    endTime: Optional[str] = None
    topic: Optional[str] = None
    tags: list[int] = Field(default_factory=list)
    audienceType: Optional[Literal["ALL_USERS", "SEGMENTED"]] = None
    weight: float = 0.0
    initialCtr: float = 15.0
    places: list[int] = Field(default_factory=list)
    included_segments: list[str] = Field(default_factory=list)
    excluded_segments: list[str] = Field(default_factory=list)
    campaign_id: Optional[int] = None
    banner_ids: list[int] = Field(default_factory=list)
    content_ids: list[int] = Field(default_factory=list)
    creative_ids: list[int] = Field(default_factory=list)