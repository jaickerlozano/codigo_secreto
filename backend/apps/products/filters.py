import django_filters
from django.db import connection
from django.http import Http404
from django.db.models import Q
from .models import Product, Category


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class ProductFilter(django_filters.FilterSet):
    category = NumberInFilter(method='filter_category')
    supplier = django_filters.NumberFilter(field_name='supplier')
    min_price = django_filters.CharFilter(method='filter_min_price')
    max_price = django_filters.CharFilter(method='filter_max_price')
    experience_level = NumberInFilter(field_name='experience_level', lookup_expr='in')
    experience_level__gte = django_filters.NumberFilter(field_name='experience_level', lookup_expr='gte')
    experience_level__lte = django_filters.NumberFilter(field_name='experience_level', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_by_search_query')
    sku = django_filters.CharFilter(field_name='sku', lookup_expr='icontains')


    class Meta:
        model = Product
        fields = ['category', 'supplier', 'min_price', 'max_price', 'experience_level', 'experience_level__gte', 'experience_level__lte', 'search', 'sku']

    # Filtra por nombre O descripción simultáneamente
    def filter_by_search_query(self, queryset, name, value):
        if not value:
            return queryset
        # 💡 Ahora que 'Q' está importado arriba, este filtro OR funcionará de inmediato
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))

    def filter_category(self, queryset, name, value):
        if not value:
            return queryset

        if Category.objects.filter(id__in=value).count() != len(set(value)):
            raise Http404("Categoría no encontrada.")

        # 'value' ahora es una lista de IDs gracias a NumberInFilter (ej:)
        # Convertimos la lista en un formato seguro para SQL nativo
        placeholders = ', '.join(['%s'] * len(value))

        with connection.cursor() as cursor:
            cursor.execute(f"""
                WITH RECURSIVE category_tree AS (
                    SELECT id FROM products_category WHERE id IN ({placeholders})
                    UNION ALL
                    SELECT c.id FROM products_category c
                    INNER JOIN category_tree ct ON c.parent_id = ct.id
                )
                SELECT id FROM category_tree
            """, list(value))
            category_ids = [row[0] for row in cursor.fetchall()]

        return queryset.filter(category__in=category_ids)

    def filter_min_price(self, queryset, name, value):
        try:
            return queryset.filter(price__gte=int(value))
        except (ValueError, TypeError):
            return queryset

    def filter_max_price(self, queryset, name, value):
        try:
            return queryset.filter(price__lte=int(value))
        except (ValueError, TypeError):
            return queryset
