from nbt.nbt import TAG_Compound, TAG_String


class BlockData:
    name: str
    properties: "list[tuple]"

    def __init__(self, item_id: str, props: "list[tuple]" = []) -> None:
        if ":" not in item_id:
            self.name = "minecraft:" + item_id
        else:
            self.name = item_id
        self.properties = props.copy()

    def __eq__(self, __o: object) -> bool:
        if __o is None:
            return False
        return self.name == __o.name and sorted(self.properties) == sorted(
            __o.properties
        )

    def copy(self) -> "BlockData":
        return BlockData(self.name, self.properties)

    def get_nbt(self) -> TAG_Compound:
        nbt_block_state = TAG_Compound()
        if any(self.properties):
            block_properties = TAG_Compound(name="Properties")
            for prop in self.properties:
                block_properties.tags.append(
                    TAG_String(name=prop[0], value=str(prop[1]))
                )
            nbt_block_state.tags.append(block_properties)
        nbt_block_state.tags.append(TAG_String(name="Name", value=self.name))
        return nbt_block_state

    @staticmethod
    def load_from_nbt(nbt: TAG_Compound()) -> "BlockData":
        name = nbt["Name"].value
        properties = []
        if "Properties" in nbt:
            properties = [(p.name, p.value) for p in nbt["Properties"].tags]
        return BlockData(name, properties)
