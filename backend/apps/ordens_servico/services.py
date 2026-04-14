from django.core.paginator import Paginator
from django.db.models import Q

from apps.ordens_servico.models import ExternalServiceOrder
from apps.unidades.models import Area
from common.enums import ExternalServiceStatus
from common.permissions import ensure_area_access, get_allowed_areas, is_global_user


def open_service_orders(area=None):
    queryset = ExternalServiceOrder.objects.select_related(
        "motor__equipment",
        "motor__equipment__area",
        "authorized_by_user",
        "registered_by_user",
    ).exclude(
        service_status=ExternalServiceStatus.RETURNED
    )
    if area is not None:
        queryset = queryset.filter(motor__equipment__area=area)
    return queryset.order_by("-sent_at")


def base_service_order_queryset(user):
    queryset = ExternalServiceOrder.objects.select_related(
        "motor__equipment",
        "motor__equipment__area",
        "authorized_by_user",
        "registered_by_user",
    ).order_by("-sent_at", "-created_at")
    allowed_areas = get_allowed_areas(user)
    if is_global_user(user):
        return queryset
    if allowed_areas:
        return queryset.filter(motor__equipment__area__in=allowed_areas)
    return queryset.none()


def resolve_area_from_code(user, area_code: str | None):
    if not area_code:
        return None
    area = Area.objects.filter(code=area_code).first()
    if area is None:
        return None
    ensure_area_access(user, area)
    return area


def apply_service_order_filters(queryset, cleaned_data: dict, *, user):
    search = (cleaned_data.get("search") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(work_order_number__icontains=search)
            | Q(vendor_name__icontains=search)
            | Q(reason__icontains=search)
            | Q(motor__unique_identifier__icontains=search)
            | Q(motor__equipment__code__icontains=search)
            | Q(motor__equipment__description__icontains=search)
        )

    status = cleaned_data.get("status")
    if status:
        queryset = queryset.filter(service_status=status)

    area = resolve_area_from_code(user, cleaned_data.get("area"))
    if area is not None:
        queryset = queryset.filter(motor__equipment__area=area)
    return queryset


def paginate_service_order_queryset(queryset, page_number):
    paginator = Paginator(queryset, 12)
    return paginator.get_page(page_number)


def serialize_query_without_page(querydict):
    params = querydict.copy()
    if "page" in params:
        params.pop("page")
    encoded = params.urlencode()
    return f"&{encoded}" if encoded else ""
