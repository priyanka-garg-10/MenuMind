from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()


class Embedder:
    """
    Thin wrapper around OpenAI's embedding API.

    Uses text-embedding-3-small (1536 dimensions).
    """

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_EMBEDDING_MODEL

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns a 1536-dimension vector."""
        text = text.replace("\n", " ").strip()
        response = await self._client.embeddings.create(
            model=self._model,
            input=[text],
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts in a single API call.
        OpenAI supports up to 2048 inputs per request.
        Results are returned in the same order as inputs.
        """
        cleaned = [t.replace("\n", " ").strip() for t in texts]
        response = await self._client.embeddings.create(
            model=self._model,
            input=cleaned,
        )
        # Sort by index to guarantee input order is preserved
        ordered = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in ordered]

    @staticmethod
    def build_menu_text(item) -> str:
        """
        Build the text that gets embedded for a menu item.

        Design rule: include every attribute a customer might describe
        when asking for a recommendation. The richer this text, the
        more accurate the semantic search results.
        """
        ingredients = ", ".join(item.ingredients or [])
        tags = ", ".join(item.tags or [])
        diet = "Vegetarian" if item.is_veg else "Non-vegetarian"

        return (
            f"{item.name}. "
            f"{item.description or ''}. "
            f"Cuisine: {item.cuisine or 'Unknown'}. "
            f"Category: {item.category or 'Unknown'}. "
            f"Ingredients: {ingredients}. "
            f"Tags: {tags}. "
            f"Spice level: {item.spice_level.value if item.spice_level else 'medium'}. "
            f"Calories: {item.calories or 0} kcal. "
            f"Protein: {item.protein_g or 0}g. "
            f"Carbs: {item.carbs_g or 0}g. "
            f"Fat: {item.fat_g or 0}g. "
            f"{diet}."
        )
