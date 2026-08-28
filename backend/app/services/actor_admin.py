"""Service layer for administrative actor domain CRUD (ECO-1603)."""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.taxonomy import get_canonical_category
from app.repositories.actor_admin import ActorAdminRepository
from app.repositories.editorial_authorization import EditorialAuthorizationRepository
from app.schemas.admin_actors import (
    AdminAccessibilityFeatureCreateSchema,
    AdminAccessibilityFeatureEnvelope,
    AdminAccessibilityFeatureListEnvelope,
    AdminAccessibilityFeatureSchema,
    AdminAccessibilityFeatureUpdateSchema,
    AdminActorCreateSchema,
    AdminActorEnvelope,
    AdminActorListEnvelope,
    AdminActorSchema,
    AdminActorTypeCreateSchema,
    AdminActorTypeEnvelope,
    AdminActorTypeListEnvelope,
    AdminActorTypeSchema,
    AdminActorTypeUpdateSchema,
    AdminActorUpdateSchema,
    AdminCategoryCreateSchema,
    AdminCategoryEnvelope,
    AdminCategoryListEnvelope,
    AdminCategorySchema,
    AdminCategoryUpdateSchema,
    AdminRouteActorCreateSchema,
    AdminRouteActorEnvelope,
    AdminRouteActorListEnvelope,
    AdminRouteActorSchema,
    AdminRouteActorUpdateSchema,
)
from app.schemas.envelopes import PaginationMeta
from app.services.editorial_authorization import (
    AuthorizationContext,
    EditorialAuthorizationService,
)


class ActorAdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ActorAdminRepository(db)
        self.auth_repo = EditorialAuthorizationRepository(db)
        self.auth_service = EditorialAuthorizationService(self.auth_repo)

    # -------------------------------------------------------------------------
    # Helper mappers
    # -------------------------------------------------------------------------

    async def _to_actor_schema(self, actor: Any) -> AdminActorSchema:
        lat, lon = await self.repo.get_actor_coordinates(actor)
        cat_schema = None
        if actor.category:
            cat_schema = AdminCategorySchema(
                id=actor.category.id,
                slug=actor.category.slug,
                label=actor.category.label,
                icon=actor.category.icon,
                color=actor.category.color,
                sort_order=actor.category.sort_order,
                created_at=actor.category.created_at,
                updated_at=actor.category.updated_at,
            )

        type_schema = None
        if getattr(actor, "type", None):
            type_schema = AdminActorTypeSchema(
                id=actor.type.id,
                category_id=actor.type.category_id,
                slug=actor.type.slug,
                label=actor.type.label,
                icon=actor.type.icon,
                sort_order=actor.type.sort_order,
                aliases=actor.type.aliases or [],
                spatial_scope=actor.type.spatial_scope,
                publication_rule=actor.type.publication_rule,
                created_at=actor.type.created_at,
                updated_at=actor.type.updated_at,
            )

        features_schemas = []
        if getattr(actor, "accessibility_features", None):
            for link in actor.accessibility_features:
                if link.feature:
                    features_schemas.append(
                        AdminAccessibilityFeatureSchema(
                            id=link.feature.id,
                            slug=link.feature.slug,
                            label=link.feature.label,
                            description=link.feature.description,
                            icon=link.feature.icon,
                            created_at=link.feature.created_at,
                            updated_at=link.feature.updated_at,
                        )
                    )

        return AdminActorSchema(
            id=actor.id,
            category_id=actor.category_id,
            category=cat_schema,
            type_id=actor.type_id,
            type=type_schema,
            slug=actor.slug,
            name=actor.name,
            description=actor.description,
            sub_category=actor.sub_category,
            address=actor.address,
            city=actor.city,
            state_code=actor.state_code,
            phone=actor.phone,
            email=actor.email,
            instagram=actor.instagram,
            website=actor.website,
            opening_hours=actor.opening_hours or {},
            payment_methods=actor.payment_methods or [],
            latitude=lat,
            longitude=lon,
            green_badge_status=actor.green_badge_status,
            verification_status=actor.verification_status,
            google_rating=float(actor.google_rating) if actor.google_rating is not None else None,
            google_review_count=actor.google_review_count,
            accessibility_features=features_schemas,
            created_at=actor.created_at,
            updated_at=actor.updated_at,
            deleted_at=actor.deleted_at,
        )

    # -------------------------------------------------------------------------
    # Actor Type Operations (Level-2 Specialized Taxonomy ADR 0015 / ECO-2504)
    # -------------------------------------------------------------------------

    async def list_actor_types(
        self, context: AuthorizationContext, category_id: uuid.UUID | None = None
    ) -> AdminActorTypeListEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        types = await self.repo.list_actor_types(category_id=category_id)
        schemas = [
            AdminActorTypeSchema(
                id=t.id,
                category_id=t.category_id,
                slug=t.slug,
                label=t.label,
                icon=t.icon,
                sort_order=t.sort_order,
                aliases=t.aliases or [],
                spatial_scope=t.spatial_scope,
                publication_rule=t.publication_rule,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in types
        ]
        return AdminActorTypeListEnvelope(data=schemas)

    async def get_actor_type(
        self, context: AuthorizationContext, type_id: uuid.UUID
    ) -> AdminActorTypeEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        t = await self.repo.get_actor_type_by_id(type_id)
        if not t:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo de ator com ID {type_id} não foi encontrado.",
            )
        return AdminActorTypeEnvelope(
            data=AdminActorTypeSchema(
                id=t.id,
                category_id=t.category_id,
                slug=t.slug,
                label=t.label,
                icon=t.icon,
                sort_order=t.sort_order,
                aliases=t.aliases or [],
                spatial_scope=t.spatial_scope,
                publication_rule=t.publication_rule,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )

    async def create_actor_type(
        self, context: AuthorizationContext, body: AdminActorTypeCreateSchema
    ) -> AdminActorTypeEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        cat = await self.repo.get_category_by_id(body.category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria vinculada (ID: {body.category_id}) não foi encontrada.",
            )

        existing = await self.repo.get_actor_type_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um tipo de ator com o slug '{body.slug}'.",
            )

        t = await self.repo.create_actor_type(
            category_id=body.category_id,
            slug=body.slug,
            label=body.label,
            icon=body.icon,
            sort_order=body.sort_order,
            aliases=body.aliases,
            spatial_scope=body.spatial_scope,
            publication_rule=body.publication_rule,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="actor_type",
            resource_id=t.id,
            changes={
                "slug": t.slug,
                "label": t.label,
                "category_id": str(t.category_id),
            },
        )

        return AdminActorTypeEnvelope(
            data=AdminActorTypeSchema(
                id=t.id,
                category_id=t.category_id,
                slug=t.slug,
                label=t.label,
                icon=t.icon,
                sort_order=t.sort_order,
                aliases=t.aliases or [],
                spatial_scope=t.spatial_scope,
                publication_rule=t.publication_rule,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )

    async def update_actor_type(
        self,
        context: AuthorizationContext,
        type_id: uuid.UUID,
        body: AdminActorTypeUpdateSchema,
    ) -> AdminActorTypeEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        t = await self.repo.get_actor_type_by_id(type_id)
        if not t:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo de ator com ID {type_id} não foi encontrado.",
            )

        if body.category_id is not None:
            cat = await self.repo.get_category_by_id(body.category_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoria vinculada (ID: {body.category_id}) não foi encontrada.",
                )

        updated = await self.repo.update_actor_type(
            type_id=type_id,
            category_id=body.category_id,
            label=body.label,
            icon=body.icon,
            sort_order=body.sort_order,
            aliases=body.aliases,
            spatial_scope=body.spatial_scope,
            publication_rule=body.publication_rule,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo de ator com ID {type_id} não foi encontrado.",
            )

        changes: dict[str, Any] = {}
        if body.label is not None:
            changes["label"] = body.label
        if body.category_id is not None:
            changes["category_id"] = str(body.category_id)

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="actor_type",
            resource_id=type_id,
            changes=changes,
        )

        return AdminActorTypeEnvelope(
            data=AdminActorTypeSchema(
                id=updated.id,
                category_id=updated.category_id,
                slug=updated.slug,
                label=updated.label,
                icon=updated.icon,
                sort_order=updated.sort_order,
                aliases=updated.aliases or [],
                spatial_scope=updated.spatial_scope,
                publication_rule=updated.publication_rule,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    # -------------------------------------------------------------------------
    # Category Operations
    # -------------------------------------------------------------------------

    async def list_categories(self, context: AuthorizationContext) -> AdminCategoryListEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        categories = await self.repo.list_categories()
        schemas = [
            AdminCategorySchema(
                id=c.id,
                slug=c.slug,
                label=c.label,
                icon=c.icon,
                color=c.color,
                sort_order=c.sort_order,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in categories
        ]
        return AdminCategoryListEnvelope(data=schemas)

    async def get_category(
        self, context: AuthorizationContext, category_id: uuid.UUID
    ) -> AdminCategoryEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        category = await self.repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria com ID {category_id} não foi encontrada.",
            )
        return AdminCategoryEnvelope(
            data=AdminCategorySchema(
                id=category.id,
                slug=category.slug,
                label=category.label,
                icon=category.icon,
                color=category.color,
                sort_order=category.sort_order,
                created_at=category.created_at,
                updated_at=category.updated_at,
            )
        )

    async def create_category(
        self, context: AuthorizationContext, body: AdminCategoryCreateSchema
    ) -> AdminCategoryEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        existing = await self.repo.get_category_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma categoria com o slug '{body.slug}'.",
            )

        category = await self.repo.create_category(
            slug=body.slug,
            label=body.label,
            icon=body.icon,
            color=body.color,
            sort_order=body.sort_order,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="category",
            resource_id=category.id,
            changes={
                "slug": category.slug,
                "label": category.label,
                "sort_order": category.sort_order,
            },
        )

        return AdminCategoryEnvelope(
            data=AdminCategorySchema(
                id=category.id,
                slug=category.slug,
                label=category.label,
                icon=category.icon,
                color=category.color,
                sort_order=category.sort_order,
                created_at=category.created_at,
                updated_at=category.updated_at,
            )
        )

    async def update_category(
        self,
        context: AuthorizationContext,
        category_id: uuid.UUID,
        body: AdminCategoryUpdateSchema,
    ) -> AdminCategoryEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        category = await self.repo.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria com ID {category_id} não foi encontrada.",
            )

        canonical = get_canonical_category(category.slug)
        resulting_metadata = (
            body.label if body.label is not None else category.label,
            body.icon if body.icon is not None else category.icon,
            body.color if body.color is not None else category.color,
            body.sort_order if body.sort_order is not None else category.sort_order,
        )
        canonical_metadata = (
            canonical["label"],
            canonical["icon"],
            canonical["color"],
            canonical["sort_order"],
        )
        if resulting_metadata != canonical_metadata:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Metadados da categoria devem corresponder à taxonomia aceita.",
            )

        updated = await self.repo.update_category(
            category_id=category_id,
            label=body.label,
            icon=body.icon,
            color=body.color,
            sort_order=body.sort_order,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria com ID {category_id} não foi encontrada.",
            )

        changes: dict[str, Any] = {}
        if body.label is not None:
            changes["label"] = body.label
        if body.icon is not None:
            changes["icon"] = body.icon
        if body.color is not None:
            changes["color"] = body.color
        if body.sort_order is not None:
            changes["sort_order"] = body.sort_order

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="category",
            resource_id=category_id,
            changes=changes,
        )

        return AdminCategoryEnvelope(
            data=AdminCategorySchema(
                id=updated.id,
                slug=updated.slug,
                label=updated.label,
                icon=updated.icon,
                color=updated.color,
                sort_order=updated.sort_order,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    # -------------------------------------------------------------------------
    # Accessibility Feature Operations
    # -------------------------------------------------------------------------

    async def list_accessibility_features(
        self, context: AuthorizationContext
    ) -> AdminAccessibilityFeatureListEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        features = await self.repo.list_accessibility_features()
        schemas = [
            AdminAccessibilityFeatureSchema(
                id=f.id,
                slug=f.slug,
                label=f.label,
                description=f.description,
                icon=f.icon,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in features
        ]
        return AdminAccessibilityFeatureListEnvelope(data=schemas)

    async def get_accessibility_feature(
        self, context: AuthorizationContext, feature_id: uuid.UUID
    ) -> AdminAccessibilityFeatureEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        feature = await self.repo.get_accessibility_feature_by_id(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Funcionalidade de acessibilidade com ID {feature_id} não foi encontrada.",
            )
        return AdminAccessibilityFeatureEnvelope(
            data=AdminAccessibilityFeatureSchema(
                id=feature.id,
                slug=feature.slug,
                label=feature.label,
                description=feature.description,
                icon=feature.icon,
                created_at=feature.created_at,
                updated_at=feature.updated_at,
            )
        )

    async def create_accessibility_feature(
        self, context: AuthorizationContext, body: AdminAccessibilityFeatureCreateSchema
    ) -> AdminAccessibilityFeatureEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        existing = await self.repo.get_accessibility_feature_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma funcionalidade de acessibilidade com o slug '{body.slug}'.",
            )

        feature = await self.repo.create_accessibility_feature(
            slug=body.slug,
            label=body.label,
            description=body.description,
            icon=body.icon,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="accessibility_feature",
            resource_id=feature.id,
            changes={"slug": feature.slug, "label": feature.label},
        )

        return AdminAccessibilityFeatureEnvelope(
            data=AdminAccessibilityFeatureSchema(
                id=feature.id,
                slug=feature.slug,
                label=feature.label,
                description=feature.description,
                icon=feature.icon,
                created_at=feature.created_at,
                updated_at=feature.updated_at,
            )
        )

    async def update_accessibility_feature(
        self,
        context: AuthorizationContext,
        feature_id: uuid.UUID,
        body: AdminAccessibilityFeatureUpdateSchema,
    ) -> AdminAccessibilityFeatureEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        feature = await self.repo.get_accessibility_feature_by_id(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Funcionalidade de acessibilidade com ID {feature_id} não foi encontrada.",
            )

        updated = await self.repo.update_accessibility_feature(
            feature_id=feature_id,
            label=body.label,
            description=body.description,
            icon=body.icon,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Funcionalidade de acessibilidade com ID {feature_id} não foi encontrada.",
            )

        changes: dict[str, Any] = {}
        if body.label is not None:
            changes["label"] = body.label
        if body.description is not None:
            changes["description"] = body.description
        if body.icon is not None:
            changes["icon"] = body.icon

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="accessibility_feature",
            resource_id=feature_id,
            changes=changes,
        )

        return AdminAccessibilityFeatureEnvelope(
            data=AdminAccessibilityFeatureSchema(
                id=updated.id,
                slug=updated.slug,
                label=updated.label,
                description=updated.description,
                icon=updated.icon,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    # -------------------------------------------------------------------------
    # Actor Operations
    # -------------------------------------------------------------------------

    async def list_actors(
        self,
        context: AuthorizationContext,
        category_id: uuid.UUID | None = None,
        type_id: uuid.UUID | None = None,
        include_deleted: bool = False,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminActorListEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        actors, total = await self.repo.list_actors(
            category_id=category_id,
            type_id=type_id,
            include_deleted=include_deleted,
            q=q,
            limit=limit,
            offset=offset,
        )

        schemas = []
        for a in actors:
            schemas.append(await self._to_actor_schema(a))

        next_cursor = str(offset + limit) if (offset + limit) < total else None
        meta = PaginationMeta(total=total, limit=limit, next_cursor=next_cursor)
        return AdminActorListEnvelope(data=schemas, meta=meta)

    async def get_actor(
        self, context: AuthorizationContext, actor_id: uuid.UUID
    ) -> AdminActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        actor = await self.repo.get_actor_by_id(actor_id, include_deleted=True)
        if not actor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )
        schema = await self._to_actor_schema(actor)
        return AdminActorEnvelope(data=schema)

    async def create_actor(
        self, context: AuthorizationContext, body: AdminActorCreateSchema
    ) -> AdminActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        # Category check
        cat = await self.repo.get_category_by_id(body.category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria vinculada (ID: {body.category_id}) não foi encontrada.",
            )

        # Slug conflict check
        existing = await self.repo.get_actor_by_slug(body.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um ator com o slug '{body.slug}'.",
            )

        # Verification check
        if body.verification_status == "verified":
            await self.auth_service.require_capability(context, "content.publish")

        # Check accessibility feature IDs validity
        if body.accessibility_feature_ids:
            for fid in body.accessibility_feature_ids:
                f_obj = await self.repo.get_accessibility_feature_by_id(fid)
                if not f_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Funcionalidade de acessibilidade (ID: {fid}) não foi encontrada.",
                    )

        # Type check if provided
        if body.type_id is not None:
            t_obj = await self.repo.get_actor_type_by_id(body.type_id)
            if not t_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tipo de ator vinculado (ID: {body.type_id}) não foi encontrado.",
                )

        actor = await self.repo.create_actor(
            category_id=body.category_id,
            type_id=body.type_id,
            slug=body.slug,
            name=body.name,
            description=body.description,
            sub_category=body.sub_category,
            address=body.address,
            city=body.city,
            state_code=body.state_code,
            phone=body.phone,
            email=body.email,
            instagram=body.instagram,
            website=body.website,
            opening_hours=body.opening_hours,
            payment_methods=body.payment_methods,
            latitude=body.latitude,
            longitude=body.longitude,
            green_badge_status=body.green_badge_status,
            verification_status=body.verification_status,
        )

        if body.accessibility_feature_ids:
            await self.repo.set_actor_accessibility_features(
                actor.id, body.accessibility_feature_ids
            )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="actor",
            resource_id=actor.id,
            changes={
                "slug": actor.slug,
                "name": actor.name,
                "category_id": str(actor.category_id),
                "type_id": str(actor.type_id) if actor.type_id else None,
                "verification_status": actor.verification_status,
            },
        )

        # Reload actor to populate relationships
        reloaded = await self.repo.get_actor_by_id(actor.id)
        schema = await self._to_actor_schema(reloaded)
        return AdminActorEnvelope(data=schema)

    async def update_actor(
        self,
        context: AuthorizationContext,
        actor_id: uuid.UUID,
        body: AdminActorUpdateSchema,
    ) -> AdminActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")

        actor = await self.repo.get_actor_by_id(actor_id, include_deleted=True)
        if not actor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )

        # Optimistic concurrency check
        if body.expected_version:
            current_version = actor.updated_at.isoformat()
            if body.expected_version != current_version:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "O ator foi alterado por outro usuário. "
                        "Por favor recarregue antes de salvar."
                    ),
                )

        # Category check if provided
        if body.category_id is not None:
            cat = await self.repo.get_category_by_id(body.category_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoria vinculada (ID: {body.category_id}) não foi encontrada.",
                )

        # Type check if provided
        if body.type_id is not None:
            t_obj = await self.repo.get_actor_type_by_id(body.type_id)
            if not t_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tipo de ator vinculado (ID: {body.type_id}) não foi encontrado.",
                )

        # Verification check
        if body.verification_status == "verified" and actor.verification_status != "verified":
            await self.auth_service.require_capability(context, "content.publish")

        # Accessibility feature check if provided
        if body.accessibility_feature_ids is not None:
            for fid in body.accessibility_feature_ids:
                f_obj = await self.repo.get_accessibility_feature_by_id(fid)
                if not f_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Funcionalidade de acessibilidade (ID: {fid}) não foi encontrada.",
                    )

        updated = await self.repo.update_actor(
            actor_id=actor_id,
            category_id=body.category_id,
            type_id=body.type_id,
            name=body.name,
            description=body.description,
            sub_category=body.sub_category,
            address=body.address,
            city=body.city,
            state_code=body.state_code,
            phone=body.phone,
            email=body.email,
            instagram=body.instagram,
            website=body.website,
            opening_hours=body.opening_hours,
            payment_methods=body.payment_methods,
            latitude=body.latitude,
            longitude=body.longitude,
            green_badge_status=body.green_badge_status,
            verification_status=body.verification_status,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )

        if body.accessibility_feature_ids is not None:
            await self.repo.set_actor_accessibility_features(
                actor_id, body.accessibility_feature_ids
            )

        changes: dict[str, Any] = {}
        if body.name is not None:
            changes["name"] = body.name
        if body.category_id is not None:
            changes["category_id"] = str(body.category_id)
        if body.verification_status is not None:
            changes["verification_status"] = body.verification_status

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="actor",
            resource_id=actor_id,
            changes=changes,
        )

        reloaded = await self.repo.get_actor_by_id(actor_id)
        schema = await self._to_actor_schema(reloaded)
        return AdminActorEnvelope(data=schema)

    async def delete_actor(
        self, context: AuthorizationContext, actor_id: uuid.UUID
    ) -> AdminActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        await self.auth_service.require_capability(context, "content.archive")

        actor = await self.repo.get_actor_by_id(actor_id, include_deleted=True)
        if not actor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )

        deleted = await self.repo.soft_delete_actor(actor_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="delete",
            resource_type="actor",
            resource_id=actor_id,
            changes={"deleted_at": deleted.deleted_at.isoformat() if deleted.deleted_at else None},
        )

        schema = await self._to_actor_schema(deleted)
        return AdminActorEnvelope(data=schema)

    # -------------------------------------------------------------------------
    # Route Actor Link Operations
    # -------------------------------------------------------------------------

    async def list_route_links_by_actor(
        self, context: AuthorizationContext, actor_id: uuid.UUID
    ) -> AdminRouteActorListEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        actor = await self.repo.get_actor_by_id(actor_id)
        if not actor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )
        links = await self.repo.list_route_actors_by_actor(actor_id)
        schemas = [
            AdminRouteActorSchema(
                id=link.id,
                route_id=link.route_id,
                actor_id=link.actor_id,
                distance_to_route_m=link.distance_to_route_m,
                route_segment_index=link.route_segment_index,
                origin_flags=link.origin_flags or {},
                is_featured=link.is_featured,
                sort_order=link.sort_order,
                created_at=link.created_at,
                updated_at=link.updated_at,
            )
            for link in links
        ]
        return AdminRouteActorListEnvelope(data=schemas)

    async def create_route_link(
        self, context: AuthorizationContext, actor_id: uuid.UUID, body: AdminRouteActorCreateSchema
    ) -> AdminRouteActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        if body.actor_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O ID do ator na URL não coincide com o corpo da requisição.",
            )

        actor = await self.repo.get_actor_by_id(actor_id)
        if not actor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ator com ID {actor_id} não foi encontrado.",
            )

        existing = await self.repo.get_route_actor_by_route_and_actor(body.route_id, actor_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O ator já está vinculado a esta rota.",
            )

        link = await self.repo.create_route_actor(
            route_id=body.route_id,
            actor_id=actor_id,
            distance_to_route_m=body.distance_to_route_m,
            route_segment_index=body.route_segment_index,
            origin_flags=body.origin_flags,
            is_featured=body.is_featured,
            sort_order=body.sort_order,
        )

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="create",
            resource_type="route_actor",
            resource_id=link.id,
            changes={
                "route_id": str(link.route_id),
                "actor_id": str(link.actor_id),
                "is_featured": link.is_featured,
            },
        )

        return AdminRouteActorEnvelope(
            data=AdminRouteActorSchema(
                id=link.id,
                route_id=link.route_id,
                actor_id=link.actor_id,
                distance_to_route_m=link.distance_to_route_m,
                route_segment_index=link.route_segment_index,
                origin_flags=link.origin_flags or {},
                is_featured=link.is_featured,
                sort_order=link.sort_order,
                created_at=link.created_at,
                updated_at=link.updated_at,
            )
        )

    async def update_route_link(
        self,
        context: AuthorizationContext,
        link_id: uuid.UUID,
        body: AdminRouteActorUpdateSchema,
    ) -> AdminRouteActorEnvelope:
        await self.auth_service.require_capability(context, "actor.write")
        link = await self.repo.get_route_actor_by_id(link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vínculo com ID {link_id} não foi encontrado.",
            )

        updated = await self.repo.update_route_actor(
            link_id=link_id,
            distance_to_route_m=body.distance_to_route_m,
            route_segment_index=body.route_segment_index,
            origin_flags=body.origin_flags,
            is_featured=body.is_featured,
            sort_order=body.sort_order,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vínculo com ID {link_id} não foi encontrado.",
            )

        changes: dict[str, Any] = {}
        if body.is_featured is not None:
            changes["is_featured"] = body.is_featured
        if body.sort_order is not None:
            changes["sort_order"] = body.sort_order

        self.auth_repo.append_audit(
            actor_id=context.actor_id,
            action="update",
            resource_type="route_actor",
            resource_id=link_id,
            changes=changes,
        )

        return AdminRouteActorEnvelope(
            data=AdminRouteActorSchema(
                id=updated.id,
                route_id=updated.route_id,
                actor_id=updated.actor_id,
                distance_to_route_m=updated.distance_to_route_m,
                route_segment_index=updated.route_segment_index,
                origin_flags=updated.origin_flags or {},
                is_featured=updated.is_featured,
                sort_order=updated.sort_order,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
            )
        )

    async def delete_route_link(self, context: AuthorizationContext, link_id: uuid.UUID) -> bool:
        await self.auth_service.require_capability(context, "actor.write")
        link = await self.repo.get_route_actor_by_id(link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vínculo com ID {link_id} não foi encontrado.",
            )

        deleted = await self.repo.delete_route_actor(link_id)
        if deleted:
            self.auth_repo.append_audit(
                actor_id=context.actor_id,
                action="delete",
                resource_type="route_actor",
                resource_id=link_id,
                changes={"deleted": True},
            )
        return deleted
