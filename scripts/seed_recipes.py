import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from app.database.session import SessionLocal

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep


SAMPLE_RECIPES: List[Dict[str, Any]] = [
    {
        "name": "Chicken Karahi",
        "slug": "chicken-karahi",
        "description": "A classic Pakistani restaurant-style chicken karahi cooked with fresh tomatoes, ginger, and aromatic spices.",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "ingredients": [
            {"name": "Chicken (bone-in pieces)", "quantity": Decimal("1000.00"), "unit": "g", "notes": "cut into medium pieces", "is_optional": False},
            {"name": "Tomatoes", "quantity": Decimal("500.00"), "unit": "g", "notes": "halved", "is_optional": False},
            {"name": "Ginger-garlic paste", "quantity": Decimal("2.00"), "unit": "tbsp", "notes": "freshly ground", "is_optional": False},
            {"name": "Green chillies", "quantity": Decimal("4.00"), "unit": "piece", "notes": "slit lengthwise", "is_optional": False},
            {"name": "Cooking oil", "quantity": Decimal("0.50"), "unit": "cup", "notes": None, "is_optional": False},
            {"name": "Red chilli flakes", "quantity": Decimal("1.50"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Black pepper (freshly crushed)", "quantity": Decimal("1.00"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Cumin powder (zeera)", "quantity": Decimal("1.00"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Coriander powder (dhaniya)", "quantity": Decimal("1.00"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Salt", "quantity": Decimal("1.50"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Fresh ginger (julienned)", "quantity": Decimal("1.00"), "unit": "tbsp", "notes": "for garnish", "is_optional": True},
            {"name": "Fresh coriander", "quantity": Decimal("2.00"), "unit": "tbsp", "notes": "chopped for garnish", "is_optional": True},
        ],
        "steps": [
            {
                "step_number": 1,
                "instruction": "Karahi mein oil garam karein aur chicken ko tez aanch par fry karein jab tak rang tabdeel na ho jaye (safaid/light golden).",
                "estimated_duration_seconds": 360,
            },
            {
                "step_number": 2,
                "instruction": "Ginger-garlic paste shamil karein aur 2 minute tak bhonain jab tak khushboo aane lage.",
                "estimated_duration_seconds": 120,
            },
            {
                "step_number": 3,
                "instruction": "Tamatar adhay kaat kar chicken par rakhain, dhak kar 8-10 minute pakayain taake tamatar narm ho jayein.",
                "estimated_duration_seconds": 600,
            },
            {
                "step_number": 4,
                "instruction": "Tamatar ka chhilka chimtay (tongs) se utaar lain aur chamchay se achi tarah mash kar lain.",
                "estimated_duration_seconds": 180,
            },
            {
                "step_number": 5,
                "instruction": "Namak, kuti laal mirch, zeera powder aur dhaniya powder daal kar tez aanch par bhonain jab tak tail alag ho jaye.",
                "estimated_duration_seconds": 300,
            },
            {
                "step_number": 6,
                "instruction": "Kuti kaali mirch aur hari mirchein daal kar 2 minute mazeed bhonain.",
                "estimated_duration_seconds": 120,
            },
            {
                "step_number": 7,
                "instruction": "Barik kata adrak aur hara dhaniya daal kar aanch band karein aur garam naan ke sath serve karein.",
                "estimated_duration_seconds": 60,
            },
        ],
    },
    {
        "name": "Tarka Daal",
        "slug": "tarka-daal",
        "description": "Comforting yellow lentils tempered with golden garlic, cumin seeds, and whole dry red chillies in ghee.",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "ingredients": [
            {"name": "Yellow lentils (moong/masoor)", "quantity": Decimal("250.00"), "unit": "g", "notes": "washed and soaked", "is_optional": False},
            {"name": "Water", "quantity": Decimal("1000.00"), "unit": "ml", "notes": None, "is_optional": False},
            {"name": "Turmeric powder (haldi)", "quantity": Decimal("0.50"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Red chilli powder", "quantity": Decimal("1.00"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Salt", "quantity": Decimal("1.00"), "unit": "tsp", "notes": None, "is_optional": False},
            {"name": "Garlic (sliced)", "quantity": Decimal("4.00"), "unit": "clove", "notes": "thinly sliced", "is_optional": False},
            {"name": "Cumin seeds (zeera)", "quantity": Decimal("1.00"), "unit": "tsp", "notes": "whole", "is_optional": False},
            {"name": "Whole dry red chillies", "quantity": Decimal("3.00"), "unit": "piece", "notes": "whole button chillies", "is_optional": False},
            {"name": "Ghee or oil", "quantity": Decimal("3.00"), "unit": "tbsp", "notes": "for tarka", "is_optional": False},
            {"name": "Fresh coriander", "quantity": Decimal("2.00"), "unit": "tbsp", "notes": "chopped for garnish", "is_optional": True},
        ],
        "steps": [
            {
                "step_number": 1,
                "instruction": "Daal ko achi tarah dho kar 15 minute ke liye paani mein bhigo dain.",
                "estimated_duration_seconds": 900,
            },
            {
                "step_number": 2,
                "instruction": "Patilay mein daal, paani, haldi, laal mirch powder aur namak daal kar ubaal anay dain.",
                "estimated_duration_seconds": 300,
            },
            {
                "step_number": 3,
                "instruction": "Aanch halki kar ke dhakkan dhaanp dain aur 15-20 minute pakayain jab tak daal narm aur gal jaye.",
                "estimated_duration_seconds": 1200,
            },
            {
                "step_number": 4,
                "instruction": "Daal ko chamchay se halka sa ghot lain taake ghul mil jaye.",
                "estimated_duration_seconds": 120,
            },
            {
                "step_number": 5,
                "instruction": "Tarka pan mein ghee garam karein, kata lehsan, zeera aur gol laal mirchein daal kar golden brown honay tak fry karein.",
                "estimated_duration_seconds": 180,
            },
            {
                "step_number": 6,
                "instruction": "Garam tarka foran daal par dalain aur foran dhakkan dhaanp dain taake khushboo bas jaye.",
                "estimated_duration_seconds": 60,
            },
            {
                "step_number": 7,
                "instruction": "Hara dhaniya chhirak kar garam chawal ya roti ke sath pesh karein.",
                "estimated_duration_seconds": 60,
            },
        ],
    },
]


def seed_database(db: Session) -> Dict[str, int]:
    """Idempotently seed the sample recipes and canonical ingredients into the database."""
    recipes_seeded = 0
    ingredients_seeded = 0

    for recipe_data in SAMPLE_RECIPES:
        slug = recipe_data["slug"]

        # 1. Fetch or create Recipe
        recipe = db.query(Recipe).filter(Recipe.slug == slug).first()
        if not recipe:
            recipe = Recipe(
                name=recipe_data["name"],
                slug=slug,
                description=recipe_data["description"],
                cuisine=recipe_data["cuisine"],
                default_servings=recipe_data["default_servings"],
                prep_time_minutes=recipe_data["prep_time_minutes"],
                cook_time_minutes=recipe_data["cook_time_minutes"],
            )
            db.add(recipe)
            db.flush()  # to obtain recipe.id
            recipes_seeded += 1
        else:
            recipe.name = recipe_data["name"]
            recipe.description = recipe_data["description"]
            recipe.cuisine = recipe_data["cuisine"]
            recipe.default_servings = recipe_data["default_servings"]
            recipe.prep_time_minutes = recipe_data["prep_time_minutes"]
            recipe.cook_time_minutes = recipe_data["cook_time_minutes"]
            # Remove existing associations for idempotent refresh
            db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
            db.query(RecipeStep).filter(RecipeStep.recipe_id == recipe.id).delete()
            db.flush()

        # 2. Ingredients & RecipeIngredient Associations
        for ing_item in recipe_data["ingredients"]:
            ing_name = ing_item["name"].strip()
            ingredient = db.query(Ingredient).filter(Ingredient.name == ing_name).first()
            if not ingredient:
                ingredient = Ingredient(name=ing_name)
                db.add(ingredient)
                db.flush()
                ingredients_seeded += 1

            assoc = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=ing_item["quantity"],
                unit=ing_item["unit"],
                notes=ing_item["notes"],
                is_optional=ing_item["is_optional"],
            )
            db.add(assoc)

        # 3. Recipe Steps
        for step_item in recipe_data["steps"]:
            step = RecipeStep(
                recipe_id=recipe.id,
                step_number=step_item["step_number"],
                instruction=step_item["instruction"],
                estimated_duration_seconds=step_item["estimated_duration_seconds"],
            )
            db.add(step)

    db.commit()
    return {
        "recipes_processed": len(SAMPLE_RECIPES),
        "new_recipes_added": recipes_seeded,
        "new_ingredients_added": ingredients_seeded,
    }


def main():
    db = SessionLocal()
    try:
        print("Starting recipe seeding...")
        result = seed_database(db)
        print(f"Seeding completed successfully: {result}")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
