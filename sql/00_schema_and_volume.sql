-- =============================================================================
-- Unity Catalog setup for the Medical Omnichannel Intelligence (Daiichi) demo.
-- Catalog `_sa701` is assumed to exist. Run first.
-- (In the actual build these were created via the MCP UC tools, which also
--  register the objects for tracking; equivalent DDL shown here for reference.)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS `_sa701`.moa
  COMMENT 'Medical Omnichannel Analytics (MOA) — synthetic Daiichi Sankyo oncology Medical Affairs data';

-- Raw source files ingested by the Lakeflow pipeline (one subfolder per dataset)
CREATE VOLUME IF NOT EXISTS `_sa701`.moa.raw
  COMMENT 'Raw synthetic Medical Affairs source files (CSV) for the Bronze layer';

-- Unstructured documents (MSL field-note PDFs, etc.)
CREATE VOLUME IF NOT EXISTS `_sa701`.moa.source_documents
  COMMENT 'Source documents (MSL field notes, etc.) for the MOA demo';

-- Governance tags (workspace enforces tag policies — values must be policy-approved)
ALTER SCHEMA `_sa701`.moa SET TAGS ('domain' = 'clinical', 'data_classification' = 'internal');
