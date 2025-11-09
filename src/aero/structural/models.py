from pydantic import Field

from geometrix.structural.common.models import StructuralElement


class Wing(StructuralElement):
    """
    Інженерний елемент, спеціалізований для крила.
    Успадковує базові жорсткості від StructuralElement та обчислює
    ефективні погонні масові характеристики.
    """
    r_offset: float = Field(0.0125, description="Відстань між центром мас та віссю зсуву (r) [м].")

    class Config:
        arbitrary_types_allowed = True

    @property
    def section(self):
        """Псевдонім для solid, щоб зберегти звичку з попереднього коду."""
        return self.solid
