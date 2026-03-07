#!/usr/bin/env python3
"""
Скрипт для проверки наличия изображений категорий
"""

import os

CATEGORIES = {
    'transport': 'Авто',
    'realestate': 'Недвижимость',
    'work': 'Работа',
    'personal': 'Одежда, обувь, аксессуары',
    'hobby': 'Хобби и отдых',
    'animals': 'Животные',
    'services': 'Услуги',
    'electronics': 'Электроника',
    'home': 'Для дома и дачи',
    'business': 'Запчасти',
    'kids': 'Товары для детей',
    'beauty': 'Красота и здоровье'
}

def check_images():
    images_dir = 'static/images/categories'
    missing = []
    found = []
    
    print("Проверка изображений категорий:\n")
    
    for slug, name in CATEGORIES.items():
        image_path = os.path.join(images_dir, f"{slug}.png")
        if os.path.exists(image_path):
            size = os.path.getsize(image_path)
            print(f"✅ {name} ({slug}.png) - {size:,} байт")
            found.append(slug)
        else:
            print(f"❌ {name} ({slug}.png) - НЕ НАЙДЕНО")
            missing.append(slug)
    
    print(f"\n📊 Статистика:")
    print(f"   Найдено: {len(found)}/{len(CATEGORIES)}")
    print(f"   Отсутствует: {len(missing)}/{len(CATEGORIES)}")
    
    if missing:
        print(f"\n⚠️  Отсутствующие изображения:")
        for slug in missing:
            print(f"   - {CATEGORIES[slug]} ({slug}.png)")
        print(f"\n💡 Поместите PNG файлы в папку: {images_dir}/")
    
    return len(missing) == 0

if __name__ == '__main__':
    check_images()
