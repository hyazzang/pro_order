import logging

from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions

from utils.response import BaseResponseMixin

from .models import Work
from .serializers import WorkCreateUpdateSerializer, WorkSerializer


class WorkListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    logger = logging.getLogger("apps")
    serializer_class = WorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "work_type",
        "assignee",
        "order__order_number",
        "due_date",
    ]
    search_fields = ["title", "description", "order__order_number"]
    ordering_fields = ["created_at", "due_date", "status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Work.objects.none()
        qs = Work.objects.select_related("assignee", "order").only(
            "id", "assignee", "order", "title", "status", "created_at"
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(assignee=self.request.user)

    @swagger_auto_schema(
        operation_summary="작업 목록 조회",
        operation_description="작업 목록을 조회합니다. (관리자는 전체, 일반 사용자는 본인에게 할당된 작업만 조회)",
        tags=["Work"],
        responses={
            200: openapi.Response("작업 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="작업 생성",
        operation_description="새로운 작업을 생성합니다. (관리자만 가능)",
        tags=["Work"],
        responses={
            201: openapi.Response("작업이 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkCreateUpdateSerializer
        return WorkSerializer

    def perform_create(self, serializer):
        # 관리자만 작업 생성 가능
        if not self.request.user.is_staff:
            self.permission_denied(self.request)

        # 담당자가 지정되지 않은 경우, 현재 요청한 관리자를 담당자로 설정
        if serializer.validated_data.get("assignee") is None:
            serializer.validated_data["assignee"] = self.request.user

        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 인스턴스를 전체 필드로 직렬화
        response_serializer = WorkSerializer(serializer.instance)
        data = response_serializer.data
        self.logger.info(f"Work created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="작업이 생성되었습니다.", status=201)


class WorkDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    logger = logging.getLogger("apps")
    serializer_class = WorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Work.objects.none()
        qs = Work.objects.select_related("assignee", "order")
        if self.request.user.is_staff:
            return qs
        return qs.filter(assignee=self.request.user)

    @swagger_auto_schema(
        operation_summary="작업 상세 조회",
        operation_description="특정 작업의 상세 정보를 조회합니다.",
        tags=["Work"],
        responses={
            200: openapi.Response("작업 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "작업을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="작업 수정",
        operation_description="작업 정보를 수정합니다. (관리자 또는 담당자만 가능)",
        tags=["Work"],
        responses={
            200: openapi.Response("작업 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "작업을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="작업 부분 수정",
        operation_description="작업 정보를 부분 수정합니다. (관리자 또는 담당자만 가능)",
        tags=["Work"],
        responses={
            200: openapi.Response("작업 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "작업을 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="작업 삭제",
        operation_description="작업을 삭제합니다. (관리자 또는 담당자만 가능)",
        tags=["Work"],
        responses={
            204: openapi.Response("작업이 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "작업을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return WorkCreateUpdateSerializer
        return WorkSerializer

    def perform_update(self, serializer):
        # 관리자만 수정 가능 (할당된 사용자도 수정 가능하게 할 경우 로직 변경 필요)
        if not self.request.user.is_staff and serializer.instance.assignee != self.request.user:
            self.permission_denied(self.request)

        # 상태가 COMPLETED로 변경되면 completed_at 설정
        if "status" in serializer.validated_data and serializer.validated_data["status"] == Work.WorkStatus.COMPLETED:
            serializer.validated_data["completed_at"] = timezone.now()
        elif "status" in serializer.validated_data and serializer.validated_data["status"] != Work.WorkStatus.COMPLETED:
            serializer.validated_data["completed_at"] = None

        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.logger.info(f"Work updated by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=serializer.data, message="작업이 수정되었습니다.")

    def perform_destroy(self, instance):
        # 관리자만 삭제 가능 (할당된 사용자도 삭제 가능하게 할 경우 로직 변경 필요)
        if not self.request.user.is_staff and instance.assignee != self.request.user:
            self.permission_denied(self.request)
        super().perform_destroy(instance)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.logger.info(f"Work deleted by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=None, message="작업이 삭제되었습니다.", status=204)
