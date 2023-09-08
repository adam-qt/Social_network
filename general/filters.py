from admin_auto_filters.filters import AutocompleteFilter


class AuthorFilter(AutocompleteFilter):
    title = 'Автор'
    field_name = 'author'


class PostFilter(AutocompleteFilter):
    title = 'Пост'
    field_name = 'post'
