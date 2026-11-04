-- =========================================================================
-- ADVANCED IT CAPSTONE: MASTER DATABASE SCHEMA
-- TEAM NAME: IRON DIH INC.
-- TARGET SYSTEM: SQLite3
-- =========================================================================


-- Enable foreign key constraint enforcement
PRAGMA foreign_keys = ON;

-- 1. BUILD SCHEMA (Create tables and foreign keys)
.read schema.sql

-- 2. POPULATE DATA (Insert mock users, books, resources, requests, donations)
.read seed_data.sql

.mode box
.header on

.print "=========================================="
.print "TEST 1: USERS & MANAGED RESOURCES"
.print "=========================================="
SELECT 
    u.user_id,
    u.username,
    u.user_role,
    cr.resource_name,
    cr.quantity_available
FROM users u
LEFT JOIN community_resources cr ON u.user_id = cr.managed_by_user_id;

.print "=========================================="
.print "TEST 2: BOOK REQUESTS BY USER"
.print "=========================================="
SELECT 
    r.request_id,
    u.username AS requester,
    r.request_title,
    r.request_author,
    r.status,
    r.request_date
FROM requests r
JOIN users u ON r.user_id = u.user_id;

.print "=========================================="
.print "TEST 3: RESOURCE DONATIONS BY DONOR"
.print "=========================================="
SELECT 
    d.donation_id,
    u.username AS donor,
    cr.resource_name,
    d.quantity_donated,
    d.notes,
    d.donation_date
FROM donations d
JOIN users u ON d.user_id = u.user_id
JOIN community_resources cr ON d.resource_id = cr.resource_id;

--==========================================
-- YAW CREATE THREE TABLES OF Fantasy, Mystery and Romance.
--==========================================