class CareSplitError(Exception):
    """Base class for errors raised by any CareSplitService implementation."""


class NotFoundError(CareSplitError):
    def __init__(self, kind: str, id: int):
        super().__init__(f"{kind} {id} not found")
        self.kind = kind
        self.id = id


class CategoryInUseError(CareSplitError):
    def __init__(self, category_id: int, expense_count: int):
        super().__init__(
            f"Category {category_id} still has {expense_count} expense(s) "
            "attached and can't be deleted"
        )
        self.category_id = category_id
        self.expense_count = expense_count


class DuplicateCategoryError(CareSplitError):
    def __init__(self, name: str):
        super().__init__(f'A category named "{name}" already exists')
        self.name = name
