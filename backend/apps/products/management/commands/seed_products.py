from django.core.management.base import BaseCommand

from apps.products.models import Category, Product, Supplier


SEED_SUPPLIER_NAME = "Código Secreto"

SEED_CATALOG = [
    # Vibradores
    {"sku": "101", "name": "Vibrador Doble Pretty Love", "category": "Vibradores", "price": 26990, "stock": 3, "level": 2, "icon": "rabbit", "gradient": "from-pink-500 to-rose-600", "features": ["Recargable", "Sumergible"], "badge": None},
    {"sku": "102", "name": "Vibrador Conejo Pretty Love", "category": "Vibradores", "price": 21990, "stock": 3, "level": 2, "icon": "heart", "gradient": "from-fuchsia-500 to-purple-600", "features": ["Recargable", "Sumergible"], "badge": None},
    {"sku": "103", "name": "Dildo 1.0 Percutor a Control Scorpio", "category": "Vibradores", "price": 30990, "stock": 3, "level": 3, "icon": "zap", "gradient": "from-violet-500 to-indigo-600", "features": ["Control remoto", "Silencioso"], "badge": None},
    {"sku": "104", "name": "Dildo Vibrador a Control Ultra Soft Love Toy", "category": "Vibradores", "price": 40990, "stock": 3, "level": 3, "icon": "flame", "gradient": "from-rose-400 to-pink-600", "features": ["Textura suave", "Control remoto"], "badge": None},
    {"sku": "105", "name": "Microfono Vibrador", "category": "Vibradores", "price": 10990, "stock": 3, "level": 1, "icon": "sparkles", "gradient": "from-magenta-500 to-fuchsia-700", "features": ["Discreto", "Ideal para principiantes"], "badge": None},
    {"sku": "106", "name": "Vibrador Curvy Fun", "category": "Vibradores", "price": 38990, "stock": 3, "level": 2, "icon": "egg", "gradient": "from-orange-500 to-red-600", "features": ["Recargable", "Sumergible"], "badge": None},
    # Anillos
    {"sku": "201", "name": "Anillo Vibrador Conejito", "category": "Anillos", "price": 12990, "stock": 3, "level": 2, "icon": "infinity", "gradient": "from-lime-500 to-green-600", "features": ["Silicona suave", "Recargable"], "badge": None},
    {"sku": "202", "name": "Kit Anillo GKP", "category": "Anillos", "price": 8990, "stock": 3, "level": 1, "icon": "circle", "gradient": "from-emerald-500 to-teal-700", "features": ["Para parejas", "Batería larga duración"], "badge": None},
    # Masturbadores
    {"sku": "301", "name": "Masturbador Arturito 2.0", "category": "Masturbadores", "price": 38990, "stock": 3, "level": 3, "icon": "box", "gradient": "from-slate-500 to-slate-700", "features": ["Textura interna", "Fácil limpieza"], "badge": None},
    {"sku": "302", "name": "Masturbador Masculino Pretty Love 360", "category": "Masturbadores", "price": 16990, "stock": 3, "level": 2, "icon": "egg", "gradient": "from-blue-500 to-cyan-600", "features": ["Rotación 360", "Recargable"], "badge": None},
    {"sku": "303", "name": "Huevitos Masturbadores", "category": "Masturbadores", "price": 5990, "stock": 3, "level": 1, "icon": "circle", "gradient": "from-purple-500 to-violet-700", "features": ["Discreto", "Portátil"], "badge": None},
    # Anal
    {"sku": "401", "name": "Plug Anal", "category": "Anal", "price": 8990, "stock": 3, "level": 1, "icon": "circle", "gradient": "from-purple-500 to-violet-700", "features": ["Silicona médica", "Base segura"], "badge": None},
    {"sku": "402", "name": "Plug Cola Conejo", "category": "Anal", "price": 9990, "stock": 3, "level": 2, "icon": "circle-dot", "gradient": "from-indigo-500 to-purple-700", "features": ["Base segura", "Fácil limpieza"], "badge": None},
    {"sku": "403", "name": "Plug Cola Zorro", "category": "Anal", "price": 9990, "stock": 3, "level": 2, "icon": "target", "gradient": "from-slate-600 to-slate-800", "features": ["Base segura", "Fácil limpieza"], "badge": None},
    # Juegos
    {"sku": "501", "name": "Juego El Teto", "category": "Juegos", "price": 8990, "stock": 3, "level": 1, "icon": "layers", "gradient": "from-fuchsia-600 to-purple-800", "features": ["Para parejas", "Diversión garantizada"], "badge": None},
    {"sku": "502", "name": "Juego Grado 3", "category": "Juegos", "price": 8990, "stock": 3, "level": 2, "icon": "package", "gradient": "from-pink-600 to-rose-800", "features": ["Para parejas", "Diversión garantizada"], "badge": None},
    {"sku": "503", "name": "Juego Diversos", "category": "Juegos", "price": 8990, "stock": 3, "level": 1, "icon": "gift", "gradient": "from-violet-500 to-fuchsia-700", "features": ["Para parejas", "Diversión garantizada"], "badge": None},
    {"sku": "504", "name": "Juego Grado 4", "category": "Juegos", "price": 8990, "stock": 3, "level": 2, "icon": "move", "gradient": "from-purple-600 to-indigo-800", "features": ["Para parejas", "Diversión garantizada"], "badge": None},
    {"sku": "505", "name": "Jenga Hot", "category": "Juegos", "price": 16990, "stock": 3, "level": 2, "icon": "flame", "gradient": "from-amber-600 to-orange-800", "features": ["Para parejas", "Diversión garantizada"], "badge": None},
    # Bondage
    {"sku": "601", "name": "Latigo Forma Pene", "category": "Bondage", "price": 4990, "stock": 3, "level": 1, "icon": "target", "gradient": "from-rose-500 to-pink-700", "features": ["Ajustable", "Resistente"], "badge": None},
    {"sku": "602", "name": "Arnes Sexual para Cama", "category": "Bondage", "price": 18990, "stock": 3, "level": 2, "icon": "anchor", "gradient": "from-red-500 to-orange-700", "features": ["Ajustable", "Resistente"], "badge": None},
    {"sku": "603", "name": "Arnes Completo", "category": "Bondage", "price": 23990, "stock": 3, "level": 3, "icon": "infinity", "gradient": "from-gray-400 to-gray-600", "features": ["Ajustable", "Resistente"], "badge": None},
    # Lubricantes
    {"sku": "701", "name": "Lubricante Manzana", "category": "Lubricantes", "price": 8990, "stock": 3, "level": 1, "icon": "droplet", "gradient": "from-sky-400 to-blue-600", "features": ["Base agua", "Comestible"], "badge": None},
    {"sku": "702", "name": "Lubricante Comestible Caramelo", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 1, "icon": "cookie", "gradient": "from-violet-400 to-fuchsia-600", "features": ["Base agua", "Comestible"], "badge": None},
    {"sku": "703", "name": "Lubricante Comestible Chocolate", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 1, "icon": "cookie", "gradient": "from-emerald-500 to-teal-700", "features": ["Base agua", "Comestible"], "badge": None},
    {"sku": "704", "name": "Lubricante Comestible Frutilla", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 1, "icon": "cherry", "gradient": "from-teal-400 to-cyan-600", "features": ["Base agua", "Comestible"], "badge": None},
    {"sku": "705", "name": "Potenciador Sexual Intense Fem", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "sparkles", "gradient": "from-pink-500 to-rose-700", "features": ["Efecto frío/calor", "Aumenta sensibilidad"], "badge": None},
    {"sku": "706", "name": "Lubricante Intimo con Efecto Calor", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "flame", "gradient": "from-orange-400 to-red-600", "features": ["Efecto calor", "Base agua"], "badge": None},
    {"sku": "707", "name": "Lubricante Intimo con Efecto Frio", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "droplet", "gradient": "from-blue-500 to-cyan-600", "features": ["Efecto frío", "Base agua"], "badge": None},
    {"sku": "708", "name": "Adormecedor y Dilatador", "category": "Lubricantes", "price": 15990, "stock": 3, "level": 2, "icon": "leaf", "gradient": "from-indigo-500 to-blue-700", "features": ["Efecto relajante", "Base agua"], "badge": None},
    {"sku": "709", "name": "Exitante Femenino Vibra+", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "zap", "gradient": "from-rose-400 to-pink-600", "features": ["Efecto estimulante", "Base agua"], "badge": None},
    {"sku": "710", "name": "Estrechante Vaginal Aprieta+", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "heart", "gradient": "from-cyan-400 to-sky-600", "features": ["Efecto estrechante", "Base agua"], "badge": None},
    {"sku": "711", "name": "Exitante Femenino Climax+", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "sparkles", "gradient": "from-green-500 to-emerald-700", "features": ["Efecto estimulante", "Base agua"], "badge": None},
    {"sku": "712", "name": "Adormecedor Anal", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "droplet", "gradient": "from-blue-600 to-indigo-800", "features": ["Efecto relajante", "Base agua"], "badge": None},
    {"sku": "713", "name": "Gel Agrandador Ballena Azul", "category": "Lubricantes", "price": 8990, "stock": 3, "level": 2, "icon": "droplet", "gradient": "from-amber-600 to-orange-800", "features": ["Efecto agrandador", "Base agua"], "badge": None},
    {"sku": "714", "name": "Potenciador Masculino Agranda+", "category": "Lubricantes", "price": 10990, "stock": 3, "level": 2, "icon": "flame", "gradient": "from-teal-500 to-emerald-700", "features": ["Efecto potenciador", "Base agua"], "badge": None},
    # Aceites y Feromonas
    {"sku": "801", "name": "Aceite Masaje Chocolate", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 1, "icon": "flower", "gradient": "from-rose-400 to-pink-600", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "802", "name": "Aceite Masaje Maracuya", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 1, "icon": "droplet", "gradient": "from-orange-400 to-red-600", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "803", "name": "Aceite Masaje Arandano", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 1, "icon": "leaf", "gradient": "from-purple-500 to-fuchsia-700", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "804", "name": "Aceite Masaje Caramelo", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 1, "icon": "cookie", "gradient": "from-blue-400 to-indigo-500", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "805", "name": "Aceite Masaje Coco", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 1, "icon": "sprout", "gradient": "from-cyan-500 to-blue-700", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "806", "name": "Aceite Masaje Chocolate Premium", "category": "Aceites y Feromonas", "price": 10990, "stock": 3, "level": 2, "icon": "flower", "gradient": "from-pink-400 to-purple-600", "features": ["Para masajes", "Aroma afrodisíaco"], "badge": None},
    {"sku": "807", "name": "Feromona Seduceme Hombre", "category": "Aceites y Feromonas", "price": 15990, "stock": 3, "level": 2, "icon": "shield", "gradient": "from-indigo-500 to-purple-700", "features": ["Atrayente", "Feromonas"], "badge": None},
    {"sku": "808", "name": "Feromona Seduceme Mujer", "category": "Aceites y Feromonas", "price": 15990, "stock": 3, "level": 2, "icon": "shield", "gradient": "from-violet-600 to-indigo-800", "features": ["Atrayente", "Feromonas"], "badge": None},
]


class Command(BaseCommand):
    help = "Crea o actualiza 44 productos semilla con el catálogo real del cliente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina los productos semilla existentes antes de recrearlos.",
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
