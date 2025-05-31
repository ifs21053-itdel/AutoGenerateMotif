from django.core.management.base import BaseCommand
from Website.models import UlosColorThread

class Command(BaseCommand):
    help = 'Seeds initial ulos color thread data into the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed ulos color data...'))

        colors_to_seed = [
            ('C001', '0, 0, 0'),
            ('C002', '353, 51, 28'),
            ('C003', '359, 91, 42'),
            ('C004', '360, 47, 69'),
            ('C005', '351, 90, 73'),
            ('C006', '348, 74, 73'),
            ('C007', '0, 63, 77'),
            ('C008', '0, 77, 86'),
            ('C009', '335, 94, 69'),
            ('C010', '331, 97, 92'),
            ('C011', '10, 80, 97'),
            ('C012', '18, 75, 44'),
            ('C013', '18, 77, 57'),
            ('C014', '34, 84, 89'),
            ('C015', '45, 100, 69'),
            ('C016', '30, 20, 100'),
            ('C017', '0, 0, 100'),
            ('C018', '50, 26, 100'),
            ('C019', '51, 100, 85'),
            ('C020', '69, 73, 79'),
            ('C021', '113, 48, 53'),
            ('C022', '132, 100, 31'),
            ('C023', '140, 100, 60'),
            ('C024', '138, 100, 93'),
            ('C025', '168, 60, 45'),
            ('C026', '200, 35, 100'),
            ('C027', '205, 60, 100'),
            ('C028', '225, 61, 70'),
            ('C029', '226, 30, 32'),
            ('C030', '248, 68, 54'),
            ('C031', '268, 57, 61')
        ]

        for code, hsv_value in colors_to_seed:
            ulos_color, created = UlosColorThread.objects.update_or_create(
                CODE=code,
                defaults={'hsv': hsv_value}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {code} - {hsv_value}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated: {code} - {hsv_value}'))

        self.stdout.write(self.style.SUCCESS('Ulos color data seeding completed successfully!'))