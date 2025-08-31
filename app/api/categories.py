from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app import crud, schemas
from app.deps import SessionDep, CurrentUser
from app.models import Category # Assuming Category model is defined

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# Helper function to build the category tree recursively
def build_category_tree(
    categories: list[Category], parent_id: UUID | None = None
) -> list[schemas.CategoryTreeOut]:
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            tree_item = schemas.CategoryTreeOut(
                id=category.id, name=category.name, children=children
            )
            tree.append(tree_item)
    return tree

@router.post(
    "/",
    response_model=schemas.CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category"
)
async def create_new_category(
    category_in: schemas.CategoryCreate,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> schemas.CategoryOut:
    """
    Creates a new product category.
    Requires authentication.
    """
    # Optional: Add superuser check here if only superusers can create categories
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    if category_in.parent_id:
        parent_category = crud.get_category_by_id(session, category_in.parent_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found."
            )

    new_category = crud.create_category(session=session, category_in=category_in)
    return new_category

@router.get(
    "/",
    response_model=list[schemas.CategoryOut],
    summary="List all categories"
)
async def list_all_categories(
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> list[schemas.CategoryOut]:
    """
    Retrieves a flat list of all product categories.
    Requires authentication.
    """
    categories = crud.get_all_categories(session=session)
    return categories

@router.get(
    "/tree",
    response_model=list[schemas.CategoryTreeOut],
    summary="Get hierarchical category tree"
)
async def get_category_tree(
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> list[schemas.CategoryTreeOut]:
    """
    Retrieves all product categories organized in a hierarchical tree structure.
    Requires authentication.
    """
    all_categories = crud.get_all_categories(session=session)
    # Sort categories to ensure parents are processed before children (optional, but good for clarity)
    # This sorting might not be strictly necessary if the build_category_tree handles it well,
    # but can help in certain ORM scenarios or for debugging.
    sorted_categories = sorted(all_categories, key=lambda c: (c.parent_id is None, c.name))
    
    tree = build_category_tree(sorted_categories)
    return tree

@router.get(
    "/{category_id}",
    response_model=schemas.CategoryOut,
    summary="Get category by ID"
)
async def get_category_details(
    category_id: UUID,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> schemas.CategoryOut:
    """
    Retrieves details of a specific category by its ID.
    Requires authentication.
    """
    category = crud.get_category_by_id(session=session, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    return category

@router.put(
    "/{category_id}",
    response_model=schemas.CategoryOut,
    summary="Update category by ID"
)
async def update_category_details(
    category_id: UUID,
    category_in: schemas.CategoryUpdate,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> schemas.CategoryOut:
    """
    Updates an existing product category.
    Requires authentication.
    """
    # Optional: Add superuser check here if only superusers can update categories
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    category = crud.get_category_by_id(session=session, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    if category_in.parent_id:
        parent_category = crud.get_category_by_id(session, category_in.parent_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found."
            )
        # Prevent a category from being its own parent or a descendant of itself (simple check)
        if category_in.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category cannot be its own parent."
            )
        # More complex check for circular dependency would require tree traversal

    updated_category = crud.update_category(session=session, category=category, category_in=category_in)
    return updated_category

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category by ID"
)
async def delete_existing_category(
    category_id: UUID,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
):
    """
    Deletes a product category.
    Requires authentication.
    """
    # Optional: Add superuser check here if only superusers can delete categories
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    category = crud.get_category_by_id(session=session, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    
    # Check for child categories to prevent orphaned children or to enforce deletion policy
    # For simplicity, we'll allow deletion, assuming SQLModel's ON DELETE CASCADE or manual handling
    # If a category has children, you might want to prevent deletion or reassign children.
    # For this example, we'll assume the database handles cascading or it's a leaf node.
    if category.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category has child categories. Please reassign or delete children first."
        )

    crud.delete_category(session=session, category=category)
    return {"message": "Category deleted successfully."}