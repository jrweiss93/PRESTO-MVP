"""Configuración del admin de Django con el sitio personalizado de Presto.

Usa `PrestoAdminSite` (dashboard de métricas) como sitio por defecto, así todos
los `@admin.register` existentes se registran en él sin cambios.
"""

from django.contrib.admin.apps import AdminConfig


class PrestoAdminConfig(AdminConfig):
    """AdminConfig que activa el sitio de admin con métricas."""

    default = True
    default_site = 'apps.reports.admin_site.site'

    def ready(self):
        """Reemplaza el sitio global antes del autodiscover y registra el admin."""
        from django.contrib import admin
        from django.contrib.admin import sites

        from apps.reports.admin_site import site

        admin.site = site
        sites.site = site
        super().ready()
