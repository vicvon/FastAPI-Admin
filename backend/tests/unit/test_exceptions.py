from common.exceptions import (
    AuthenticationError,
    ExternalServiceError,
    InfrastructureError,
    PermissionError,
)


def test_authentication_error_defaults() -> None:
    exc = AuthenticationError()

    assert exc.code == 401
    assert exc.message == "认证失败"


def test_permission_error_defaults() -> None:
    exc = PermissionError()

    assert exc.code == 403
    assert exc.message == "无权限执行该操作"


def test_infrastructure_error_defaults() -> None:
    exc = InfrastructureError()

    assert exc.code == 500
    assert exc.message == "基础设施异常"


def test_external_service_error_defaults() -> None:
    exc = ExternalServiceError()

    assert exc.code == 502
    assert exc.message == "外部依赖异常"
