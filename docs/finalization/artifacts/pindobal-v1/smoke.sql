-- ECO-1505 read-only smoke. Execute only after environment fingerprint approval.
select count(*) as regions
from app_private.regions where slug = 'santarem-belterra';

select count(*) as routes
from app_private.routes where slug = 'rota-pindobal';

select o.code, extensions.ST_NPoints(g.geometry::extensions.geometry) as points,
       g.distance_m, extensions.ST_SRID(g.geometry::extensions.geometry) as srid
from app_private.route_geometries g
join app_private.route_origins o on o.id = g.route_origin_id
join app_private.routes r on r.id = o.route_id
where r.slug = 'rota-pindobal'
order by o.sort_order;

select count(*) as route_actors, count(distinct ra.actor_id) as unique_actors
from app_private.route_actors ra
join app_private.routes r on r.id = ra.route_id
where r.slug = 'rota-pindobal';

select count(*) as invented_google_place_ids
from app_private.actor_external_refs ref
join app_private.external_sources src on src.id = ref.source_id
where src.slug = 'google-places-legacy-pindobal-v1'
  and ref.external_id is not null;
