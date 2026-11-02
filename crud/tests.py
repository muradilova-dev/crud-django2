from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Item


class ItemModelTests(TestCase):
    """Тесты модели Item."""

    # __str__ возвращает название
    def test_str_returns_title(self):
        item = Item.objects.create(title='Заметка', description='Текст')
        self.assertEqual(str(item), 'Заметка')

    # get_absolute_url ведёт на детальную страницу
    def test_get_absolute_url(self):
        item = Item.objects.create(title='Заметка')
        self.assertEqual(item.get_absolute_url(), reverse('crud:detail', args=[item.pk]))

    # Описание необязательное: по умолчанию пустая строка
    def test_description_is_optional(self):
        item = Item.objects.create(title='Без описания')
        self.assertEqual(item.description, '')

    # Даты создания и изменения заполняются автоматически
    def test_dates_are_set_automatically(self):
        item = Item.objects.create(title='С датами')
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)

    # У новой записи появляется id (pk)
    def test_new_item_gets_pk(self):
        item = Item.objects.create(title='Заметка')
        self.assertIsNotNone(item.pk)


class ItemCreateTests(TestCase):
    """Тесты создания записи (Create)."""

    def setUp(self):
        self.url = reverse('crud:create')

    # Форма создания открывается и использует нужный шаблон
    def test_create_form_opens(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_form.html')

    # В форме есть поля title и description
    def test_create_form_has_fields(self):
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIn('title', form.fields)
        self.assertIn('description', form.fields)

    # POST с корректными данными создаёт запись и делает редирект на detail
    def test_create_valid_post(self):
        response = self.client.post(self.url, {'title': 'Новая', 'description': 'Текст'})
        item = Item.objects.get(title='Новая')
        self.assertRedirects(response, reverse('crud:detail', args=[item.pk]))
        self.assertEqual(Item.objects.count(), 1)

    # В базу сохраняются именно те данные, которые отправили
    def test_create_saves_correct_data(self):
        self.client.post(self.url, {'title': 'Заголовок', 'description': 'Описание'})
        item = Item.objects.get()
        self.assertEqual(item.title, 'Заголовок')
        self.assertEqual(item.description, 'Описание')

    # Запись можно создать без описания
    def test_create_without_description(self):
        self.client.post(self.url, {'title': 'Только название'})
        self.assertEqual(Item.objects.count(), 1)

    # POST без названия не создаёт запись и показывает ошибку формы
    def test_create_invalid_empty_title(self):
        response = self.client.post(self.url, {'title': '', 'description': 'Текст'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.assertEqual(Item.objects.count(), 0)

    # Название из одних пробелов тоже считается пустым
    def test_create_invalid_spaces_title(self):
        response = self.client.post(self.url, {'title': '     '})
        self.assertIn('title', response.context['form'].errors)
        self.assertEqual(Item.objects.count(), 0)

    # Название длиннее 200 символов не принимается, ровно 200 принимается
    def test_create_title_max_length(self):
        self.client.post(self.url, {'title': 'а' * 201})
        self.assertEqual(Item.objects.count(), 0)
        self.client.post(self.url, {'title': 'а' * 200})
        self.assertEqual(Item.objects.count(), 1)


class ItemListTests(TestCase):
    """Тесты списка записей (Read - список)."""

    # Страница списка открывается и использует нужный шаблон
    def test_list_returns_200_and_template(self):
        response = self.client.get(reverse('crud:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_list.html')

    # Созданные записи видны в списке
    def test_list_shows_items(self):
        Item.objects.create(title='Первая')
        Item.objects.create(title='Вторая')
        response = self.client.get(reverse('crud:list'))
        self.assertContains(response, 'Первая')
        self.assertContains(response, 'Вторая')
        self.assertEqual(len(response.context['items']), 2)

    # Пустой список показывает заглушку
    def test_list_empty(self):
        response = self.client.get(reverse('crud:list'))
        self.assertContains(response, 'Записей пока нет.')
        self.assertEqual(len(response.context['items']), 0)

    # В списке есть ссылки на detail, update и delete каждой записи
    def test_list_has_links_for_each_item(self):
        item = Item.objects.create(title='Заметка')
        response = self.client.get(reverse('crud:list'))
        self.assertContains(response, reverse('crud:detail', args=[item.pk]))
        self.assertContains(response, reverse('crud:update', args=[item.pk]))
        self.assertContains(response, reverse('crud:delete', args=[item.pk]))

    # Новые записи идут в списке первыми
    def test_list_newest_first(self):
        old = Item.objects.create(title='Старая')
        new = Item.objects.create(title='Новая')
        Item.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse('crud:list'))
        items = list(response.context['items'])
        self.assertEqual(items[0].pk, new.pk)
        self.assertEqual(items[1].pk, old.pk)

    # Ссылка из списка реально открывает нужную запись
    def test_list_link_opens_detail(self):
        item = Item.objects.create(title='Заметка', description='Её текст')
        response = self.client.get(reverse('crud:detail', args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Её текст')


class ItemDetailTests(TestCase):
    """Тесты детальной страницы (Read - одна запись)."""

    def setUp(self):
        self.item = Item.objects.create(title='Заметка', description='Описание заметки')
        self.url = reverse('crud:detail', args=[self.item.pk])

    # Детальная страница показывает данные записи
    def test_detail_shows_item(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заметка')
        self.assertContains(response, 'Описание заметки')

    # Используется нужный шаблон
    def test_detail_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'crud/item_detail.html')

    # id объекта в контексте совпадает с запрошенным
    def test_detail_context_has_correct_item(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['item'].pk, self.item.pk)

    # На странице есть ссылки на изменение и удаление
    def test_detail_has_update_and_delete_links(self):
        response = self.client.get(self.url)
        self.assertContains(response, reverse('crud:update', args=[self.item.pk]))
        self.assertContains(response, reverse('crud:delete', args=[self.item.pk]))

    # Несуществующий id даёт 404
    def test_detail_404(self):
        response = self.client.get(reverse('crud:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # Вместо числа в URL буквы - 404
    def test_detail_invalid_id_type_404(self):
        response = self.client.get('/crud/abc/')
        self.assertEqual(response.status_code, 404)


class ItemUpdateTests(TestCase):
    """Тесты изменения записи (Update)."""

    def setUp(self):
        self.item = Item.objects.create(title='Старое', description='Старый текст')
        self.url = reverse('crud:update', args=[self.item.pk])

    # Форма изменения открывается и уже заполнена данными записи
    def test_update_form_is_prefilled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Старое')
        self.assertContains(response, 'Старый текст')

    # POST меняет данные записи в базе и делает редирект на detail
    def test_update_valid_post(self):
        response = self.client.post(self.url, {'title': 'Новое', 'description': 'Новый текст'})
        self.assertRedirects(response, reverse('crud:detail', args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Новое')
        self.assertEqual(self.item.description, 'Новый текст')

    # При обновлении новая запись не создаётся, количество не меняется
    def test_update_does_not_create_new_item(self):
        self.client.post(self.url, {'title': 'Новое', 'description': 'Текст'})
        self.assertEqual(Item.objects.count(), 1)

    # Пустое название не принимается, данные в базе остаются прежними
    def test_update_invalid_post_keeps_old_data(self):
        response = self.client.post(self.url, {'title': '', 'description': 'Другое'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Старое')
        self.assertEqual(self.item.description, 'Старый текст')

    # Изменение одной записи не трогает другие
    def test_update_does_not_touch_other_items(self):
        other = Item.objects.create(title='Чужая', description='Не менять')
        self.client.post(self.url, {'title': 'Новое', 'description': 'Текст'})
        other.refresh_from_db()
        self.assertEqual(other.title, 'Чужая')
        self.assertEqual(other.description, 'Не менять')

    # Дата создания не меняется, дата изменения не уменьшается
    def test_update_dates(self):
        created = self.item.created_at
        updated = self.item.updated_at
        self.client.post(self.url, {'title': 'Новое', 'description': 'Текст'})
        self.item.refresh_from_db()
        self.assertEqual(self.item.created_at, created)
        self.assertGreaterEqual(self.item.updated_at, updated)

    # Изменение несуществующей записи даёт 404
    def test_update_404(self):
        response = self.client.get(reverse('crud:update', args=[9999]))
        self.assertEqual(response.status_code, 404)


class ItemDeleteTests(TestCase):
    """Тесты удаления записи (Delete)."""

    def setUp(self):
        self.item = Item.objects.create(title='Удаляемая')
        self.url = reverse('crud:delete', args=[self.item.pk])

    # Страница подтверждения удаления открывается
    def test_delete_confirm_page_opens(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_confirm_delete.html')
        self.assertContains(response, 'Удаляемая')

    # GET-запрос запись не удаляет, она удаляется только по POST
    def test_delete_get_does_not_delete(self):
        self.client.get(self.url)
        self.assertEqual(Item.objects.count(), 1)

    # POST удаляет запись и возвращает на список
    def test_delete_post_removes_item(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('crud:list'))
        self.assertEqual(Item.objects.count(), 0)

    # После удаления страница записи отдаёт 404
    def test_delete_then_detail_is_404(self):
        self.client.post(self.url)
        response = self.client.get(reverse('crud:detail', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)

    # Удаление одной записи не трогает другие
    def test_delete_keeps_other_items(self):
        other = Item.objects.create(title='Остаётся')
        self.client.post(self.url)
        self.assertEqual(Item.objects.count(), 1)
        self.assertTrue(Item.objects.filter(pk=other.pk).exists())

    # Удаление несуществующей записи даёт 404
    def test_delete_404(self):
        response = self.client.post(reverse('crud:delete', args=[9999]))
        self.assertEqual(response.status_code, 404)


class ItemFullCycleTests(TestCase):
    """Сквозной тест: весь цикл CRUD подряд."""

    # Создать -> прочитать -> изменить -> удалить
    def test_full_crud_cycle(self):
        # Create
        response = self.client.post(reverse('crud:create'),
                                    {'title': 'Цикл', 'description': 'Начало'}, follow=True)
        self.assertEqual(response.status_code, 200)
        item = Item.objects.get(title='Цикл')
        # Read
        self.assertContains(response, 'Начало')
        self.assertContains(self.client.get(reverse('crud:list')), 'Цикл')
        # Update
        response = self.client.post(reverse('crud:update', args=[item.pk]),
                                    {'title': 'Цикл 2', 'description': 'Конец'}, follow=True)
        self.assertContains(response, 'Цикл 2')
        # Delete
        response = self.client.post(reverse('crud:delete', args=[item.pk]), follow=True)
        self.assertContains(response, 'Записей пока нет.')
        self.assertEqual(Item.objects.count(), 0)
