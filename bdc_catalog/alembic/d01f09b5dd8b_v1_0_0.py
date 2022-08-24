"""BDC-Catalog to v1.0.0

See more in CHANGES.rst

Revision ID: d01f09b5dd8b
Revises: 561ebe6266ad
Create Date: 2022-06-08 12:06:57.476168

"""
from alembic import op
import geoalchemy2.types
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from bdc_db.sqltypes import JSONB

# revision identifiers, used by Alembic.
revision = 'd01f09b5dd8b'
down_revision = 'c68b17b1860b'
branch_labels = ()
depends_on = '561ebe6266ad'  # LCCS-DB stable 0.8.1


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('processors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('facility', sa.String(length=255), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('uri', sa.String(length=255), nullable=True),
        sa.Column('metadata', JSONB('bdc-catalog/processor.json', astext_type=sa.Text()), nullable=True, comment='Follow the JSONSchema @jsonschemas/application-metadata.json'),
        sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('processors_pkey')),
        sa.UniqueConstraint('name', 'version', name=op.f('processors_name_key')),
        schema='bdc'
    )
    op.create_table('items_processors',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('processor_id', sa.Integer(), nullable=False),
        sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['bdc.items.id'], name=op.f('items_processors_item_id_items_fkey'), onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['processor_id'], ['bdc.processors.id'], name=op.f('items_processors_processor_id_processors_fkey'), onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id', 'processor_id', name=op.f('items_processors_pkey')),
        schema='bdc'
    )
    op.drop_column('items', 'application_id', schema='bdc')
    op.drop_table('applications', schema='bdc')

    # Bands
    with op.batch_alter_table('bands', schema='bdc') as bands_op:
        bands_op.alter_column(column_name='scale', new_column_name='scale_mult')
        bands_op.add_column(sa.Column('scale_add', sa.Numeric(), nullable=True,
                                      comment='The value to sum in scale mult'))

        sql = """UPDATE bdc.bands 
        SET metadata = coalesce(metadata::jsonb,'{}'::jsonb) || ('{\"eo\":{\"resolution_x\":'||resolution_x||',\"resolution_y\":'||resolution_y||',\"center_wavelength\":'||center_wavelength||',\"full_width_half_max\": '||full_width_half_max||'}}')::jsonb"""
        bands_op.execute(sql)
        bands_op.drop_column('center_wavelength')
        bands_op.drop_column('full_width_half_max')
        bands_op.drop_column('resolution_x')
        bands_op.drop_column('resolution_y')

    op.create_index(op.f('idx_bdc_bands_resolution_unit_id'), 'bands', ['resolution_unit_id'], unique=False,
                    schema='bdc')

    bind = op.get_bind()
    collection_category_type = postgresql.ENUM('eo', 'sar', 'lidar', 'unknown', name='collection_category_type')
    collection_category_type.create(bind)

    provider_role_type = postgresql.ENUM('licensor', 'producer', 'processor', 'host', name='provider_role_type')
    provider_role_type.create(bind)

    # Collections
    with op.batch_alter_table('collections', schema='bdc') as collection_op:
        collection_op.add_column(sa.Column('keywords', sa.ARRAY(sa.String()), nullable=True))
        collection_op.add_column(sa.Column('properties', JSONB('bdc-catalog/collection-properties.json'),
                                           nullable=True,
                                           comment='Contains the properties offered by STAC collections'))
        collection_op.add_column(sa.Column('summaries', JSONB('bdc-catalog/collection-summaries.json'),
                                           nullable=True,
                                           comment='Contains the STAC Collection summaries.'))
        collection_op.add_column(sa.Column('item_assets', JSONB('bdc-catalog/collection-item-assets.json'),
                                           nullable=True,
                                           comment='Contains the STAC Extension Item Assets.'))
        collection_op.add_column(sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        collection_op.add_column(sa.Column('category',
                                           sa.Enum('eo', 'sar', 'lidar', 'unknown', name='collection_category_type'),
                                           nullable=False,
                                           server_default='eo'))
        collection_op.alter_column(column_name='extent', new_column_name='spatial_extent')
        collection_op.alter_column(column_name='version',
                                   existing_type=sa.INTEGER(),
                                   type_=sa.String(),
                                   existing_nullable=False,)

    op.drop_index('idx_bdc_collections_extent', table_name='collections', schema='bdc')
    op.create_index(op.f('idx_bdc_collections_category'), 'collections', ['category'], unique=False, schema='bdc')
    op.create_index(op.f('idx_bdc_collections_is_available'), 'collections', ['is_available'], unique=False, schema='bdc')
    op.create_index(op.f('idx_bdc_collections_is_public'), 'collections', ['is_public'], unique=False, schema='bdc')
    op.create_index(op.f('idx_bdc_collections_spatial_extent'), 'collections', ['spatial_extent'], unique=False, schema='bdc', postgresql_using='gist')
    op.create_index(op.f('idx_bdc_collections_start_date'), 'collections', ['start_date', 'end_date'], unique=False, schema='bdc')

    # For Collection Providers table, identify version 0.8.0 before
    op.execute('CREATE TABLE IF NOT EXISTS bdc.collections_providers_legacy AS '
               '(SELECT * FROM bdc.collections_providers)')

    op.add_column('collections_providers',
                  sa.Column('roles', sa.ARRAY(sa.Enum('licensor', 'producer', 'processor', 'host',
                                              name='provider_role_type')),
                            nullable=False, server_default='{"host"}'), schema='bdc')
    op.create_index(op.f('idx_bdc_collections_providers_roles'), 'collections_providers', ['roles'], unique=False, schema='bdc')
    op.drop_column('collections_providers', 'active', schema='bdc')
    op.drop_column('collections_providers', 'priority', schema='bdc')

    # Items
    with op.batch_alter_table('items', schema='bdc') as item_op:
        item_op.alter_column(column_name='geom', new_column_name='bbox')
        item_op.alter_column(column_name='min_convex_hull', new_column_name='footprint')
        item_op.add_column(sa.Column('is_public', sa.Boolean(), server_default=sa.text('true'), nullable=False))
        item_op.add_column(sa.Column('is_available', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    op.drop_index('idx_bdc_items_geom', table_name='items', schema='bdc')
    op.drop_index('idx_bdc_items_min_convex_hull', table_name='items', schema='bdc')
    op.create_index(op.f('idx_bdc_items_bbox'), 'items', ['bbox'], unique=False, schema='bdc', postgresql_using='gist')
    op.create_index(op.f('idx_bdc_items_footprint'), 'items', ['footprint'], unique=False, schema='bdc', postgresql_using='gist')
    op.create_index(op.f('idx_bdc_items_is_available'), 'items', ['is_available'], unique=False, schema='bdc')
    op.create_index(op.f('idx_bdc_items_is_public'), 'items', ['is_public'], unique=False, schema='bdc')
    op.create_index(op.f('idx_bdc_items_metadata'), 'items', ['metadata'], unique=False, schema='bdc')
    op.drop_constraint('items_srid_spatial_ref_sys_fkey', 'items', schema='bdc', type_='foreignkey')

    op.execute('ALTER TABLE bdc.items DROP CONSTRAINT IF EXISTS items_application_id_applications_fkey')

    op.create_foreign_key(op.f('items_srid_spatial_ref_sys_fkey'), 'items', 'spatial_ref_sys', ['srid'], ['srid'], source_schema='bdc', referent_schema='public', onupdate='CASCADE', ondelete='CASCADE')

    op.execute('ALTER TABLE bdc.items DROP COLUMN IF EXISTS application_id')

    # For Providers table 0.8.x
    op.execute('CREATE TABLE IF NOT EXISTS bdc.providers_legacy AS '
               '(SELECT * FROM bdc.providers)')

    op.add_column('providers', sa.Column('url', sa.String(length=255), nullable=True), schema='bdc')
    op.drop_column('providers', 'credentials', schema='bdc')
    op.drop_column('providers', 'uri', schema='bdc')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('providers', schema='bdc') as provider_op:
        provider_op.add_column(sa.Column('uri', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        provider_op.add_column(sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()),
                                         autoincrement=False, nullable=True,
                                         comment='Follow the JSONSchema @jsonschemas/provider-credentials.json'))
        provider_op.drop_column('url')

    with op.batch_alter_table('items', schema='bdc') as item_op:
        item_op.alter_column(column_name='bbox', new_column_name='geom')
        item_op.alter_column(column_name='footprint', new_column_name='min_convex_hull')
        item_op.drop_column('is_available')
        item_op.drop_column('is_public')
        item_op.add_column(sa.Column('application_id', sa.INTEGER(), autoincrement=False, nullable=True))

    op.create_table(
        'applications',
        sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('bdc.applications_id_seq'::regclass)"),
                  autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
        sa.Column('version', sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        sa.Column('uri', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True,
                  comment='Follow the JSONSchema @jsonschemas/application-metadata.json'),
        sa.Column('created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                  nullable=False),
        sa.Column('updated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False,
                  nullable=False),
        sa.PrimaryKeyConstraint('id', name='applications_pkey'),
        sa.UniqueConstraint('name', 'version', name='applications_name_key'),
        schema='bdc'
    )

    op.create_foreign_key('items_application_id_applications_fkey', 'items', 'applications', ['application_id'], ['id'],
                          source_schema='bdc', referent_schema='bdc', onupdate='CASCADE', ondelete='CASCADE')

    op.drop_constraint(op.f('items_srid_spatial_ref_sys_fkey'), 'items', schema='bdc', type_='foreignkey')
    op.create_foreign_key('items_srid_spatial_ref_sys_fkey', 'items', 'spatial_ref_sys', ['srid'], ['srid'], source_schema='bdc', onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('idx_bdc_items_metadata'), table_name='items', schema='bdc')

    op.drop_index(op.f('idx_bdc_items_footprint'), table_name='items', schema='bdc', postgresql_using='gist')
    op.drop_index(op.f('idx_bdc_items_bbox'), table_name='items', schema='bdc', postgresql_using='gist')
    op.create_index('idx_bdc_items_min_convex_hull', 'items', ['min_convex_hull'], unique=False, schema='bdc',  postgresql_using='gist')
    op.create_index('idx_bdc_items_geom', 'items', ['geom'], unique=False, schema='bdc', postgresql_using='gist')

    # Collection Providers/Providers: TODO: Use legacy tables to fill data
    op.add_column('collections_providers',
                  sa.Column('priority', sa.SMALLINT(), autoincrement=False, nullable=False, server_default='1'),
                  schema='bdc')
    op.add_column('collections_providers',
                  sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=False, server_default='true'),
                  schema='bdc')
    op.drop_index(op.f('idx_bdc_collections_providers_roles'), table_name='collections_providers', schema='bdc')
    op.drop_column('collections_providers', 'roles', schema='bdc')
    op.add_column('collections',
                  sa.Column('extent', geoalchemy2.types.Geometry(
                      geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT',
                      name='geometry', spatial_index=False
                  ), autoincrement=False, nullable=True), schema='bdc')
    op.drop_index(op.f('idx_bdc_collections_start_date'), table_name='collections', schema='bdc')
    op.drop_index(op.f('idx_bdc_collections_spatial_extent'), table_name='collections', schema='bdc', postgresql_using='gist')
    op.drop_index(op.f('idx_bdc_collections_is_public'), table_name='collections', schema='bdc')
    op.drop_index(op.f('idx_bdc_collections_is_available'), table_name='collections', schema='bdc')
    op.drop_index(op.f('idx_bdc_collections_category'), table_name='collections', schema='bdc')
    op.create_index('idx_bdc_collections_extent', 'collections', ['extent'], unique=False, schema='bdc', postgresql_using='gist')

    with op.batch_alter_table('collections', schema='bdc') as collection_op:
        collection_op.alter_column('version',
                                   existing_type=sa.String(),
                                   type_=sa.INTEGER(),
                                   existing_nullable=False,
                                   postgresql_using='version::INTEGER')
        collection_op.drop_column('spatial_extent')
        collection_op.drop_column('category')
        collection_op.drop_column('is_available')
        collection_op.drop_column('item_assets')
        collection_op.drop_column('summaries')
        collection_op.drop_column('properties')
        collection_op.drop_column('keywords')

    bind = op.get_bind()
    collection_category_type = postgresql.ENUM('eo', 'sar', 'lidar', 'unknown', name='collection_category_type')
    collection_category_type.drop(bind, checkfirst=False)
    postgresql.ENUM(name='provider_role_type').drop(bind)

    with op.batch_alter_table('bands', schema='bdc') as band_op:
        band_op.add_column(sa.Column('resolution_y', sa.NUMERIC(), autoincrement=False, nullable=True))
        band_op.add_column(sa.Column('resolution_x', sa.NUMERIC(), autoincrement=False, nullable=True))
        band_op.add_column(sa.Column('full_width_half_max', sa.NUMERIC(), autoincrement=False, nullable=True))
        band_op.add_column(sa.Column('center_wavelength', sa.NUMERIC(), autoincrement=False, nullable=True))
        band_op.drop_column('scale_add')
        band_op.alter_column(column_name='scale_mult', new_column_name='scale')

    op.drop_index(op.f('idx_bdc_bands_resolution_unit_id'), table_name='bands', schema='bdc')

    op.drop_table('items_processors', schema='bdc')
    op.drop_table('processors', schema='bdc')
    # ### end Alembic commands ###