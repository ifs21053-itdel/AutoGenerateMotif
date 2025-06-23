from django.core.management.base import BaseCommand
from Website.models import UlosColorThread

class Command(BaseCommand):
    help = 'Seeds initial ulos color thread data into the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed ulos color data...'))

        colors_to_seed = [
            ('C001', '0, 0, 0'),
            ('C002', '353, 51, 28'),
            ('C003', '18, 75, 44'),
            ('C004', '18, 77, 57'),
            ('C005', '30, 20, 100'),
            ('C006', '0, 0, 100'),
            ('C007', '359, 91, 55'),
            ('C008', '351, 90, 73'),
            ('C009', '335, 94, 69'),
            ('C010', '348, 74, 73'),
            ('C011', '0, 63, 77'),
            ('C012', '360, 47, 69'),
            ('C013', '331, 97, 92'),
            ('C014', '0, 77, 86'),
            ('C015', '10, 80, 97'),
            ('C016', '34, 84, 89'),
            ('C017', '45, 100, 69'),
            ('C018', '51, 100, 85'),
            ('C019', '50, 26, 100'),
            ('C020', '132, 100, 31'),
            ('C021', '168, 60, 45'),
            ('C022', '113, 48, 53'),
            ('C023', '140, 100, 60'),
            ('C024', '138, 100, 93'),
            ('C025', '69, 73, 79'),
            ('C026', '268, 57, 61'),
            ('C027', '226, 30, 32'),
            ('C028', '248, 68, 54'),
            ('C029', '225, 61, 70'),
            ('C030', '205, 60, 100'),
            ('C031', '200, 35, 100')
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