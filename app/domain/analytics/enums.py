from enum import StrEnum


class AnalyticsEventType(StrEnum):
    PAGE_VIEWED = "page_viewed"

    PRODUCT_VIEWED = "product_viewed"
    PRODUCT_SELECTED = "product_selected"

    SEARCH_PERFORMED = "search_performed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"

    CATEGORY_VIEWED = "category_viewed"
    BRAND_VIEWED = "brand_viewed"

    RECOMMENDATION_VIEWED = "recommendation_viewed"
    RECOMMENDATION_CLICKED = "recommendation_clicked"

    OUTFIT_VIEWED = "outfit_viewed"
    OUTFIT_ITEM_SELECTED = "outfit_item_selected"

    CART_CREATED = "cart_created"
    CART_LINE_ADDED = "cart_line_added"
    CART_LINE_REMOVED = "cart_line_removed"

    CHECKOUT_STARTED = "checkout_started"
    ORDER_COMPLETED = "order_completed"

    WISHLIST_ADDED = "wishlist_added"
    WISHLIST_REMOVED = "wishlist_removed"


class AnalyticsSource(StrEnum):
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    SYSTEM = "system"


class MetricType(StrEnum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    RATE = "rate"


class AggregationPeriod(StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
