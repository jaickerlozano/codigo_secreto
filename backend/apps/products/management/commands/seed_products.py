from django.core.management.base import BaseCommand

from apps.products.models import Category, Product, Supplier


SEED_SUPPLIER_NAME = "Código Secreto"

SEED_CATALOG = [
    # Doble estimulación
    {"sku": "101", "name": "Vibrador Conejo Remoto", "category": "Doble estimulación", "price": 59990, "stock": 25, "level": 3, "icon": "rabbit", "gradient": "from-pink-500 to-rose-600", "features": ["10 modos", "Recargable USB", "Sumergible"], "badge": "Más vendido"},
    {"sku": "102", "name": "Huevo Vibrador Doble", "category": "Doble estimulación", "price": 34990, "stock": 30, "level": 2, "icon": "egg", "gradient": "from-fuchsia-500 to-purple-600", "features": ["Control remoto", "Silencioso"], "badge": None},
    {"sku": "103", "name": "Masajeador Wand Recargable", "category": "Doble estimulación", "price": 69990, "stock": 18, "level": 4, "icon": "wand", "gradient": "from-violet-500 to-indigo-600", "features": ["Potente", "Cabezal flexible"], "badge": "Premium"},
    {"sku": "104", "name": "Vibrador de Lengua", "category": "Doble estimulación", "price": 44990, "stock": 22, "level": 3, "icon": "tongue", "gradient": "from-rose-400 to-pink-600", "features": ["Movimiento ondulante", "Sumergible"], "badge": None},
    {"sku": "105", "name": "Estimulador de Clítoris", "category": "Doble estimulación", "price": 52990, "stock": 28, "level": 3, "icon": "sparkles", "gradient": "from-magenta-500 to-fuchsia-700", "features": ["Succión + vibración", "Recargable"], "badge": "Nuevo"},
    {"sku": "106", "name": "Vibrador Realista Recargable", "category": "Doble estimulación", "price": 62990, "stock": 15, "level": 4, "icon": "flame", "gradient": "from-orange-500 to-red-600", "features": ["Textura realista", "Vibración multivel"], "badge": None},
    {"sku": "107", "name": "Mini Vibrador Bala", "category": "Doble estimulación", "price": 19990, "stock": 50, "level": 1, "icon": "zap", "gradient": "from-cyan-500 to-blue-600", "features": ["Discreto", "Ideal para principiantes"], "badge": None},
    {"sku": "108", "name": "Succionador 2 en 1", "category": "Doble estimulación", "price": 74990, "stock": 12, "level": 4, "icon": "heart", "gradient": "from-pink-600 to-rose-800", "features": ["Doble estimulación", "App opcional"], "badge": "Top"},
    {"sku": "109", "name": "Anillo Vibrador Pareja", "category": "Doble estimulación", "price": 24990, "stock": 40, "level": 2, "icon": "infinity", "gradient": "from-lime-500 to-green-600", "features": ["Para parejas", "Batería larga duración"], "badge": None},
    # Anal
    {"sku": "110", "name": "Plug Anal Silicona Pequeño", "category": "Anal", "price": 17990, "stock": 35, "level": 1, "icon": "circle", "gradient": "from-purple-500 to-violet-700", "features": ["Silicona médica", "Base segura"], "badge": "Ideal primerizos"},
    {"sku": "111", "name": "Plug Anal Mediano", "category": "Anal", "price": 22990, "stock": 28, "level": 2, "icon": "circle", "gradient": "from-indigo-500 to-purple-700", "features": ["Textura suave", "Fácil limpieza"], "badge": None},
    {"sku": "112", "name": "Plug Anal Grande", "category": "Anal", "price": 28990, "stock": 20, "level": 4, "icon": "circle", "gradient": "from-slate-600 to-slate-800", "features": ["Experiencia avanzada", "Base ancha"], "badge": None},
    {"sku": "113", "name": "Kit Plugs Anales 3 Piezas", "category": "Anal", "price": 45990, "stock": 16, "level": 3, "icon": "package", "gradient": "from-fuchsia-600 to-purple-800", "features": ["3 tamaños", "Estuche incluido"], "badge": "Pack"},
    {"sku": "114", "name": "Bolas Anales Silicona", "category": "Anal", "price": 26990, "stock": 24, "level": 2, "icon": "circle-dot", "gradient": "from-pink-500 to-rose-700", "features": ["Entrenamiento progresivo", "Extracción fácil"], "badge": None},
    {"sku": "115", "name": "Dildo Anal Curvo", "category": "Anal", "price": 54990, "stock": 14, "level": 4, "icon": "target", "gradient": "from-violet-600 to-indigo-800", "features": ["Curva ergonómica", "Ventosa"], "badge": None},
    {"sku": "116", "name": "Lubricante Anal Extra Lubricante", "category": "Gel Anal", "price": 15990, "stock": 60, "level": 2, "icon": "droplet", "gradient": "from-blue-500 to-cyan-600", "features": ["Larga duración", "Base agua"], "badge": None},
    {"sku": "117", "name": "Anillo Anal Vibrador", "category": "Anal", "price": 32990, "stock": 19, "level": 3, "icon": "circle", "gradient": "from-rose-500 to-pink-700", "features": ["Vibración suave", "Silicona"], "badge": None},
    # Doble penetración
    {"sku": "118", "name": "Arnés Doble Penetración", "category": "Doble penetración", "price": 58990, "stock": 11, "level": 4, "icon": "layers", "gradient": "from-fuchsia-600 to-purple-800", "features": ["Ajustable", "Compatible con consoladores"], "badge": None},
    {"sku": "119", "name": "Consolador Doble Flexible", "category": "Doble penetración", "price": 47990, "stock": 13, "level": 3, "icon": "move", "gradient": "from-pink-600 to-rose-800", "features": ["Doble estimulación", "Flexibilidad total"], "badge": None},
    {"sku": "120", "name": "Vibrador Doble Recargable", "category": "Doble penetración", "price": 67990, "stock": 10, "level": 4, "icon": "battery-charging", "gradient": "from-violet-500 to-fuchsia-700", "features": ["2 motores", "Recargable"], "badge": "Premium"},
    {"sku": "121", "name": "Dildo Strapless", "category": "Doble penetración", "price": 55990, "stock": 12, "level": 4, "icon": "anchor", "gradient": "from-purple-600 to-indigo-800", "features": ["Sin arnés", "Estimulación mutua"], "badge": None},
    # Oral
    {"sku": "122", "name": "Anillo para el Pene Vibratorio", "category": "Oral", "price": 21990, "stock": 33, "level": 2, "icon": "circle", "gradient": "from-lime-500 to-emerald-600", "features": ["Retarda y vibra", "Para ambos"], "badge": None},
    {"sku": "123", "name": "Masturbador Masculino", "category": "Oral", "price": 46990, "stock": 21, "level": 3, "icon": "box", "gradient": "from-slate-500 to-slate-700", "features": ["Textura interna", "Fácil limpieza"], "badge": "Nuevo"},
    {"sku": "124", "name": "Lubricante Sabor Fresa", "category": "Gel Sabores", "price": 11990, "stock": 70, "level": 1, "icon": "cherry", "gradient": "from-red-400 to-pink-600", "features": ["Comestible", "Base agua"], "badge": None},
    {"sku": "125", "name": "Gel Oral Calor Intenso", "category": "Gel Estimulante", "price": 13990, "stock": 55, "level": 2, "icon": "flame", "gradient": "from-orange-400 to-red-600", "features": ["Efecto calor", "Para oral"], "badge": None},
    # Preservativos
    {"sku": "126", "name": "Preservativos Ultra Delgados x12", "category": "Preservativos", "price": 8990, "stock": 100, "level": 1, "icon": "shield", "gradient": "from-blue-400 to-indigo-500", "features": ["Máxima sensibilidad", "Resistentes"], "badge": None},
    {"sku": "127", "name": "Preservativos Texturados x10", "category": "Preservativos", "price": 9990, "stock": 90, "level": 1, "icon": "shield", "gradient": "from-cyan-500 to-blue-700", "features": ["Puntos y estrías", "Lubricados"], "badge": None},
    {"sku": "128", "name": "Preservativos Retardantes x12", "category": "Preservativos", "price": 10990, "stock": 85, "level": 2, "icon": "shield", "gradient": "from-teal-500 to-emerald-700", "features": ["Efecto retardante", "Lubricados"], "badge": None},
    {"sku": "129", "name": "Preservativos Sabores Mixtos x24", "category": "Preservativos", "price": 12990, "stock": 80, "level": 1, "icon": "shield", "gradient": "from-pink-400 to-purple-600", "features": ["Variedad de sabores", "Pack económico"], "badge": "Pack"},
    # Lubricantes y geles
    {"sku": "130", "name": "Lubricante Base Agua 100ml", "category": "Lubricantes", "price": 10990, "stock": 95, "level": 1, "icon": "droplet", "gradient": "from-sky-400 to-blue-600", "features": ["Base agua", "Compatible con juguetes"], "badge": None},
    {"sku": "131", "name": "Lubricante Silicona 100ml", "category": "Lubricantes", "price": 14990, "stock": 75, "level": 2, "icon": "droplet", "gradient": "from-violet-400 to-fuchsia-600", "features": ["Larga duración", "No pegajoso"], "badge": None},
    {"sku": "132", "name": "Gel Anal Relajante 150ml", "category": "Gel Anal", "price": 16990, "stock": 65, "level": 2, "icon": "leaf", "gradient": "from-emerald-500 to-teal-700", "features": ["Efecto relajante", "Base agua"], "badge": None},
    {"sku": "133", "name": "Gel Neutro Hipoalergénico", "category": "Gel Neutro", "price": 11990, "stock": 88, "level": 1, "icon": "shield-check", "gradient": "from-gray-400 to-gray-600", "features": ["Hipoalergénico", "Sin perfume"], "badge": None},
    {"sku": "134", "name": "Gel Estimulante Femenino", "category": "Gel Estimulante", "price": 13990, "stock": 72, "level": 2, "icon": "sparkles", "gradient": "from-pink-500 to-rose-700", "features": ["Efecto frío/calor", "Aumenta sensibilidad"], "badge": None},
    {"sku": "135", "name": "Gel Retardante Masculino", "category": "Gel Retardante", "price": 14990, "stock": 68, "level": 2, "icon": "clock", "gradient": "from-indigo-500 to-blue-700", "features": ["Retarda la eyaculación", "Seguro con preservativos"], "badge": None},
    {"sku": "136", "name": "Gel Sabores Chocolate", "category": "Gel Sabores", "price": 11990, "stock": 74, "level": 1, "icon": "cookie", "gradient": "from-amber-600 to-orange-800", "features": ["Comestible", "Sabor chocolate"], "badge": None},
    {"sku": "137", "name": "Lubricante Natural Orgánico", "category": "Lubricantes", "price": 15990, "stock": 60, "level": 1, "icon": "leaf", "gradient": "from-green-500 to-emerald-700", "features": ["Ingredientes naturales", "Vegano"], "badge": "Natural"},
    {"sku": "138", "name": "Gel Calor Intenso", "category": "Gel Estimulante", "price": 13990, "stock": 58, "level": 3, "icon": "flame", "gradient": "from-red-500 to-orange-700", "features": ["Efecto calor intenso", "Para parejas"], "badge": None},
    {"sku": "139", "name": "Lubricante Aloe Vera", "category": "Lubricantes", "price": 12990, "stock": 82, "level": 1, "icon": "droplet", "gradient": "from-teal-400 to-cyan-600", "features": ["Aloe vera", "Hidratante"], "badge": None},
    {"sku": "140", "name": "Gel Anal Extra Lubricante", "category": "Gel Anal", "price": 17990, "stock": 56, "level": 2, "icon": "droplet", "gradient": "from-blue-600 to-indigo-800", "features": ["Extra lubricación", "No se seca"], "badge": None},
    {"sku": "141", "name": "Aceite Masajes Eróticos", "category": "Lubricantes", "price": 18990, "stock": 48, "level": 2, "icon": "flower", "gradient": "from-rose-400 to-pink-600", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "142", "name": "Preservativo + Lubricante Pack", "category": "Preservativos", "price": 19990, "stock": 45, "level": 1, "icon": "gift", "gradient": "from-violet-500 to-fuchsia-700", "features": ["Pack parejas", "Ahorro"], "badge": "Pack"},
    {"sku": "143", "name": "Lubricante Sabor Menta", "category": "Gel Sabores", "price": 11990, "stock": 77, "level": 1, "icon": "sprout", "gradient": "from-emerald-400 to-green-600", "features": ["Sabor menta", "Refrescante"], "badge": None},
    {"sku": "144", "name": "Gel Intimo Hidratante", "category": "Gel Neutro", "price": 10990, "stock": 66, "level": 1, "icon": "droplet", "gradient": "from-cyan-400 to-sky-600", "features": ["Hidratación diaria", "PH equilibrado"], "badge": None},
]


class Command(BaseCommand):
    help = "Crea o actualiza 44 productos semilla con SKUs 101-144."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los productos semilla existentes (SKU 101-144) antes de recrearlos.",
        )

    def handle(self, *args, **options):
        supplier, _ = Supplier.objects.get_or_create(
            name=SEED_SUPPLIER_NAME,
            defaults={
                "contact": "Atención al Cliente",
                "email": "hola@codigosecreto.cl",
                "phone": "+56900000000",
                "address": "Santiago, Chile",
            },
        )

        seed_skus = {item["sku"] for item in SEED_CATALOG}

        if options["reset"]:
            deleted, _ = Product.objects.filter(sku__in=seed_skus).delete()
            self.stdout.write(
                self.style.WARNING(f"Eliminados {deleted} productos semilla existentes.")
            )

        created_count = 0
        updated_count = 0

        for item in SEED_CATALOG:
            category, _ = Category.objects.get_or_create(
                name=item["category"],
                defaults={"description": f"Categoría {item['category']}"},
            )

            defaults = {
                "name": item["name"],
                "description": f"{item['name']}: producto de la categoría {item['category']}.",
                "category": category,
                "supplier": supplier,
                "price": item["price"],
                "current_stock": item["stock"],
                "minimum_stock": 5,
                "icon": item["icon"],
                "gradient": item["gradient"],
                "experience_level": item["level"],
                "features": item["features"],
                "badge": item["badge"],
            }

            product, created = Product.objects.update_or_create(
                sku=item["sku"],
                defaults=defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {created_count} productos creados, {updated_count} actualizados. "
                f"Total en catálogo: {Product.objects.count()}."
            )
        )
