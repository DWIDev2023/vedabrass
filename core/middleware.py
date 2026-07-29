from django.shortcuts import render


class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        status_code = response.status_code

        if status_code in [400, 403, 404, 405, 408, 419, 500, 503]:
            admin_paths = [
                "/master/",
                "/dashboard/",
                "/backend/",
            ]

            is_admin = any(
                request.path.startswith(path)
                for path in admin_paths
            )

            template = (
                f"errors/admin/{status_code}.html"
                if is_admin
                else f"errors/web/{status_code}.html"
            )

            return render(
                request,
                template,
                status=status_code
            )

        return response