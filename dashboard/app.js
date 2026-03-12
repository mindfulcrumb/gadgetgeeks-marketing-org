/**
 * GadgetGeeks HQ — God Mode Office Simulator v2
 * Full pixel-art office with walls, doors, furniture, break room,
 * meeting room, coffee machine, water cooler, and living characters.
 */

// ═══════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════
const REPO = 'mindfulcrumb/gadgetgeeks-marketing-org';
const RAW = `https://raw.githubusercontent.com/${REPO}/main`;
const T = 32;          // tile size
const COLS = 35;
const ROWS = 23;
const W = COLS * T;    // 1120
const H = ROWS * T;    // 736

// ═══════════════════════════════════════════
// TILE MAP  (0=floor 1=wall 2=door)
// 35 wide x 23 tall
// ═══════════════════════════════════════════
// prettier-ignore
const MAP = [
// 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], // 0
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 1  LOBBY
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 2
  [1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1], // 3  wall row
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], // 4
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], // 5
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], // 6
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], // 7
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], // 8
  [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1], // 9  wall row
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 10
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 11
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 12
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 13
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 14
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1], // 15
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 16
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 17
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 18
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 19
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 20
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], // 21
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], // 22
];

/*
  FLOOR PLAN:
  Row 0: outer wall
  Rows 1-2: LOBBY / Reception (full width)
  Row 3: wall with doors
  Rows 4-8: INTEL (1-7) | SEO (9-13) | hallway (14-20) | CONTENT (22-26, through door at 26) → wait, let me reconsider
  Actually the map is:
    cols 1-7: INTEL room (rows 4-8)
    cols 9-13: SEO room (rows 4-8)
    cols 15-20: HALLWAY (open, with break area)
    cols 22-26: SOCIAL room (rows 4-8) → actually looking at map, door at 26, room 28-33
    cols 28-33: SOCIAL room (rows 4-8) → door at col 32

  Let me re-read my map more carefully:
  Row 3 walls: 1s at 0-6, door at 7, 1s at 8-12, door at 13, 1s at 14-17, open at 18-19, 1s at 21-25, door at 26, 1s at 27-31, door at 32, 1s at 33-34

  So rooms top row:
  - cols 1-7, rows 4-8: Room A (INTEL) - door at (7,3)
  - cols 9-13, rows 4-8: Room B (SEO) - door at (13,3)
  - cols 15-20, rows 4-8: Open hallway / break area
  - cols 22-26: Wait... wall at 21, then 22-26 open, door at 26... no.

  Actually looking again at row 3:
  [1,1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,0,0,0,1,1,1,1,1,2,1,1,1,1,1,2,1,1]
   0 1 2 3 4 5 6 7 8 9 ...12 13 14..17 18-20 21 22..25 26 27..31 32 33 34

  So: wall 0-6, door 7, wall 8-12, door 13, wall 14-17, floor 18-20, wall 21-25, door 26, wall 27-31, door 32, wall 33-34

  Rooms (top):
  - INTEL: cols 1-7, rows 4-8 (door into lobby at col 7, row 3)
  - SEO: cols 9-13, rows 4-8 (door at col 13, row 3)
  - Open passage: cols 18-20 connecting lobby to mid hallway
  - CONTENT: cols 22-26, rows 4-8 (door at col 26, row 3)
  - EMAIL: cols 28-33, rows 4-8 (door at col 32, row 3)

  Row 9 walls:
  [1,1,1,1,1,1,2,1,1,1,1,1,2,1,1,0,0,0,0,0,0,1,1,1,1,2,1,1,1,1,1,2,1,1,1]
   0 1 2 3 4 5 6 7 8 9..11 12 13 14 15-20 21 22..23 24 25 26 27..30 31 32..34

  Rooms (bottom left):
  - SOCIAL: cols 1-7, rows 10-14 (door at col 6, row 9)
  - CRO: cols 9-13, rows 10-14 (door at col 12, row 9)
  - Main hallway: cols 15-20, rows 10-14
  - MEETING ROOM: cols 22-26 → wait let me check: wall 21, 22-23, door 24? No...

  Actually: wall 21, 22-23 wall, 24 door? No: 1,1,1,1,2,1,1 → 21=1, 22=1, 23=1, 24=1, 25=2(door), 26=1, 27=1
  Wait: starting from index 21: 1,1,1,1,2,1,1,1,1,1,2,1,1,1
  That's 21=1, 22=1, 23=1, 24=1, 25=2, 26=1, 27=1, 28=1, 29=1, 30=1, 31=2, 32=1, 33=1, 34=1

  Hmm that doesn't match either. Let me count row 9 carefully:
  Index: 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34
  Value: 1  1  1  1  1  1  2  1  1  1  1  1  2  1  1  0  0  0  0  0  0  1  1  1  1  2  1  1  1  1  1  2  1  1  1

  OK so:
  - wall 0-5, door 6, wall 7-11, door 12, wall 13-14, floor 15-20, wall 21-23, door 24... no, 24=2? No: 21=1,22=1,23=1,24=1,25=2...
  Wait I need to count more carefully. The array has commas, let me just count positions:
  1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1
  pos0=1, pos1=1, ..., pos6=2, pos7=1, ..., pos12=2, pos13=1, pos14=1, pos15-20=0, pos21=1, pos22=1, pos23=1, pos24=1, pos25=2, pos26=1, pos27=1, pos28=1, pos29=1, pos30=1, pos31=2, pos32=1, pos33=1, pos34=1

  Bottom rooms:
  - SOCIAL: cols 1-5, rows 10-14 (door col 6, row 9) — but wall at col 7-8...
  Actually col 7=1, col 8=1 so:
  - Room left: cols 1-6(door)-7(wall) → room is cols 1-7, door at 6
  Wait, col 7 is wall in row 9. But in rows 10-14, col 8 is wall (from row 4-8 map: col 8 = 1). Let me check row 10:
  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
  So walls at 0, 8, 21, 34.  Room: cols 1-7 (rows 10-14), cols 9-20 (open — that's hallway + break area), cols 22-33 (big room).

  OK so:
  Bottom-left room (SOCIAL): cols 1-7, rows 10-14. Door at (6, 9).
  Bottom-mid: cols 9-13 is a room with wall at col 8 and... wait row 10 has wall only at 0, 8, 21, 34. So cols 9-20 is one big open area. That's the hallway/break room!

  And then row 9: door at 12 means there's a room cols 9-13 in rows 4-8 (SEO) with a door down at (12,9) into the hallway. But in rows 10+, cols 9-20 is open.

  OK and for rows 10-14, the right side: wall at 21, then cols 22-33 is open, wall at 34.
  Row 9 has door at 25 and door at 31, with walls between. But rows 10-14 show cols 22-33 as all open (one big room).

  Hmm, this means for rows 10-14: there are two rooms separated by wall at col 21:
  - Left: cols 1-7 (SOCIAL room)
  - Middle: cols 9-20 (big open hallway / break area)
  - Right: cols 22-33 (one big room — but row 9 suggests two doors, maybe it's subdivided in row 9 only?)

  Hmm actually looking at row 9: 21=1, 22=1, 23=1, 24=1, 25=2, 26=1, 27=1...31=2...
  This means the wall at row 9 between cols 21-34 creates two doors: one at 25 and one at 31. But in row 10, cols 22-33 are all floor. So the wall at row 9 just has two entry points into one big room. That's fine — it's a meeting room / GM office.

  But wait, row 15 subdivides further:
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1]
  Walls: 0-8, floor 9-20, wall 21-27, door 28, wall 29-34

  So rows 16-21:
  - Left side: cols 1-8 wall at top (row 15), but row 16 shows: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, ...] — col 0=wall, cols 1-20 = floor, col 21 = wall
  That means cols 1-20 is one massive room (GM office / lounge) for rows 16-21
  - Right side: cols 22-33 for rows 16-21, door at col 28 row 15 — that's the GM office

  OK I think my map works! Let me define the rooms clearly:
*/

// Room definitions (for labels, furniture placement, colors)
const ROOMS = [
  // Top row offices
  { id: 'intel',   label: 'INTEL',        x:1,  y:4,  w:7,  h:5,  color:'#00ccff', doorX:7,  doorY:3 },
  { id: 'seo',     label: 'SEO',          x:9,  y:4,  w:5,  h:5,  color:'#00ff88', doorX:13, doorY:3 },
  { id: 'content', label: 'CONTENT',      x:22, y:4,  w:5,  h:5,  color:'#ff8844', doorX:26, doorY:3 },
  { id: 'email',   label: 'EMAIL',        x:28, y:4,  w:6,  h:5,  color:'#ffcc00', doorX:32, doorY:3 },
  // Bottom left
  { id: 'social',  label: 'SOCIAL',       x:1,  y:10, w:7,  h:5,  color:'#ff66aa', doorX:6,  doorY:9 },
  // Right big room split
  { id: 'cro',     label: 'CRO',          x:22, y:10, w:12, h:5,  color:'#4488ff', doorX:25, doorY:9 },
  // X Intel (war room in hallway area)
  { id: 'x_intel', label: 'X WAR ROOM',   x:15, y:4,  w:6,  h:5,  color:'#1DA1F2', doorX:18, doorY:3 },
  // GM corner office (bottom right)
  { id: 'gm',      label: 'GM OFFICE',    x:22, y:16, w:12, h:6,  color:'#aa66ff', doorX:28, doorY:15 },
];

// Special areas
const LOBBY    = { x:1, y:1, w:33, h:2, label:'RECEPTION' };
const HALLWAY  = { x:15, y:4, w:6, h:11 };  // central open area rows 4-14
const BREAKROOM = { x:1, y:16, w:20, h:6, label:'BREAK ROOM' };
const MEETING  = { x:9, y:10, w:12, h:5, label:'MEETING ROOM' };

// Furniture items (drawn on canvas)
const FURNITURE = [
  // Lobby
  { type:'reception_desk', x:15, y:1, w:5, h:1 },
  { type:'plant', x:1, y:1 }, { type:'plant', x:33, y:1 },
  { type:'plant', x:1, y:2 }, { type:'plant', x:33, y:2 },
  // Company sign on lobby wall
  { type:'sign', x:16, y:0, text:'GADGETGEEKS' },

  // Break room
  { type:'coffee',  x:2,  y:17 },
  { type:'cooler',  x:4,  y:17 },
  { type:'couch',   x:7,  y:18, w:3 },
  { type:'couch',   x:7,  y:20, w:3 },
  { type:'table',   x:12, y:18, w:2, h:2 },
  { type:'vending', x:18, y:17 },
  { type:'plant',   x:1,  y:21 },
  { type:'plant',   x:20, y:21 },

  // Meeting room
  { type:'conf_table', x:12, y:11, w:6, h:3 },
  { type:'whiteboard', x:9,  y:10, w:4 },
  { type:'plant', x:20, y:10 },
  { type:'plant', x:9,  y:14 },

  // Hallway decorations
  { type:'plant', x:15, y:4 }, { type:'plant', x:20, y:4 },
  { type:'plant', x:15, y:8 }, { type:'plant', x:20, y:8 },
  { type:'printer', x:17, y:7 },
  { type:'board',   x:15, y:3, w:3, text:'SCHEDULE' },

  // Room furniture — each office gets desk, chair, bookshelf, plant
  // INTEL
  { type:'desk', x:3, y:5, dir:'down' },
  { type:'bookshelf', x:1, y:4 }, { type:'bookshelf', x:1, y:5 },
  { type:'plant', x:7, y:8 },
  { type:'monitor', x:3, y:5, screen:'cyan' },
  // SEO
  { type:'desk', x:10, y:5, dir:'down' },
  { type:'bookshelf', x:13, y:4 },
  { type:'plant', x:9, y:8 },
  { type:'monitor', x:10, y:5, screen:'green' },
  // CONTENT
  { type:'desk', x:24, y:5, dir:'down' },
  { type:'bookshelf', x:22, y:4 },
  { type:'plant', x:26, y:8 },
  { type:'monitor', x:24, y:5, screen:'orange' },
  // EMAIL
  { type:'desk', x:30, y:5, dir:'down' },
  { type:'bookshelf', x:33, y:4 },
  { type:'plant', x:28, y:8 },
  { type:'monitor', x:30, y:5, screen:'yellow' },
  // SOCIAL
  { type:'desk', x:3, y:11, dir:'down' },
  { type:'bookshelf', x:1, y:10 },
  { type:'plant', x:7, y:14 },
  { type:'monitor', x:3, y:11, screen:'pink' },
  // CRO
  { type:'desk', x:25, y:11, dir:'down' },
  { type:'bookshelf', x:33, y:10 },
  { type:'plant', x:22, y:14 },
  { type:'monitor', x:25, y:11, screen:'blue' },
  // X-INTEL (ECHO sits in the hallway war room area)
  { type:'desk', x:16, y:5, dir:'down' },
  { type:'monitor', x:16, y:5, screen:'xblue' },
  // GM OFFICE
  { type:'desk_large', x:27, y:18, w:3 },
  { type:'bookshelf', x:22, y:16 }, { type:'bookshelf', x:22, y:17 },
  { type:'couch', x:23, y:20, w:3 },
  { type:'plant', x:33, y:16 }, { type:'plant', x:33, y:21 },
  { type:'monitor', x:28, y:18, screen:'purple' },
  { type:'board', x:30, y:16, w:3, text:'RULES' },
];

// ═══════════════════════════════════════════
// EMPLOYEES
// ═══════════════════════════════════════════
const EMPLOYEES = [
  {
    id:'intel', name:'SCOUT', fullName:'Scout Reeves',
    title:'Market Intelligence Analyst', dept:'Intel Division',
    color:'#00ccff', hair:'#1a6680', skin:'#d4a574', pants:'#2a2a5a', shoes:'#1a1a3a',
    schedule:'Mon/Thu 10:47 UTC', cronDays:[1,4], cronH:10, cronM:47,
    stateKeys:['intel'], deskTile:{x:3,y:6}, roomId:'intel',
    tasks:['Monitor 5 competitor stores','Scrape customer language (Reddit, Amazon)','Detect refurb market trends','Update competitor pricing','Feed insights to SEO + Content'],
    rules:['Never fabricate data','Git audit trail on all findings','Flag urgent moves to GM'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Web Scraping',icon:'🌐',color:'#0ea5e9'}],
    dataFlow:{reads:['config/competitors-list.json','config/niche.json'],writes:['departments/intel/competitors.json','departments/intel/trends.json','departments/intel/customer-language.json'],feeds:['SEO','Content','Social','Email']},
  },
  {
    id:'seo', name:'PIXEL', fullName:'Pixel Chen',
    title:'SEO Specialist', dept:'Search Division',
    color:'#00ff88', hair:'#0a5530', skin:'#c68642', pants:'#1a3a2a', shoes:'#1a1a3a',
    schedule:'Daily 6:23 + Mon deep audit', cronDays:[0,1,2,3,4,5,6], cronH:6, cronM:23,
    stateKeys:['seo','seo_weekly'], deskTile:{x:10,y:6}, roomId:'seo',
    tasks:['Daily: optimize top keyword opportunity','Weekly: full keyword research','Audit JSON-LD structured data','Monitor ranking movements','Feed keyword data to Content'],
    rules:['Shopify products READ ONLY','Real Shopify data only','Title < 60, desc < 155 chars'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Shopify GraphQL',icon:'🛍️',color:'#96bf48'}],
    dataFlow:{reads:['departments/intel/trends.json','departments/intel/customer-language.json','config/niche.json'],writes:['departments/seo/keywords.json','departments/seo/opportunities.json'],feeds:['Content']},
  },
  {
    id:'content', name:'QUILL', fullName:'Quill Navarro',
    title:'Content Creator', dept:'Content Division',
    color:'#ff8844', hair:'#804420', skin:'#e8beac', pants:'#4a3020', shoes:'#2a1a0a',
    schedule:'Mon/Wed/Fri 7:41 UTC', cronDays:[1,3,5], cronH:7, cronM:41,
    stateKeys:['content'], deskTile:{x:24,y:6}, roomId:'content',
    tasks:['Write blog posts & guides','Product descriptions from Shopify','Pre-Write Protocol (Schwartz levels)','23-check anti-AI self-audit','Must pass Copy Police scanner'],
    rules:['0 banned words (68 blocklist)','0 AI patterns','Specifics > superlatives','3-round Critic loop on all copy'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'CrewAI Pipeline',icon:'🔗',color:'#7c3aed'}],
    dataFlow:{reads:['departments/intel/customer-language.json','departments/x-intel/daily-brief.json','departments/seo/keywords.json','config/copy-rules.json'],writes:['departments/content/calendar.json','departments/content/drafts/'],feeds:['Social','Email']},
  },
  {
    id:'email', name:'BEACON', fullName:'Beacon Torres',
    title:'Email Marketing Specialist', dept:'Email Division',
    color:'#ffcc00', hair:'#3a2a00', skin:'#8d5524', pants:'#3a3a1a', shoes:'#2a2a0a',
    schedule:'Tue/Thu 8:53 UTC', cronDays:[2,4], cronH:8, cronM:53,
    stateKeys:['email'], deskTile:{x:30,y:6}, roomId:'email',
    tasks:['Design campaigns (welcome, promo, winback)','Plan A/B tests','Segment customers','Anti-AI copy check','Queue for human approval'],
    rules:['NEVER auto-send — queue ONLY','Preview + test send required','Subject < 50 chars','CAN-SPAM compliant'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Resend',icon:'📧',color:'#00b4d8'},{name:'Shopify GraphQL',icon:'🛍️',color:'#96bf48'}],
    dataFlow:{reads:['departments/intel/customer-language.json','departments/x-intel/daily-brief.json','config/copy-rules.json'],writes:['departments/email/campaigns.json','departments/email/ab-tests.json'],feeds:['Queue (human approval)']},
  },
  {
    id:'social', name:'VIBE', fullName:'Vibe Santiago',
    title:'Social Media Manager', dept:'Social Division',
    color:'#ff66aa', hair:'#802050', skin:'#d4a574', pants:'#4a1a3a', shoes:'#2a0a1a',
    schedule:'Daily 9:11 + 16:37 UTC', cronDays:[0,1,2,3,4,5,6], cronH:9, cronM:11,
    stateKeys:['social_morning','social_afternoon'], deskTile:{x:3,y:12}, roomId:'social',
    tasks:['AM: create 1-2 posts via Postiz','PM: check engagement','Platform-native content','Use Intel customer language','Track top performers'],
    rules:['Platform-specific voice','Brand-safe only','Anti-AI on all content','Per-platform hashtags'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Postiz',icon:'📱',color:'#e11d48'},{name:'X API v2',icon:'𝕏',color:'#1DA1F2'}],
    dataFlow:{reads:['departments/intel/trends.json','departments/x-intel/daily-brief.json','departments/content/calendar.json','config/copy-rules.json'],writes:['departments/social/calendar.json','departments/social/engagement-log.md'],feeds:['Postiz → All platforms']},
  },
  {
    id:'cro', name:'METRIC', fullName:'Metric Okafor',
    title:'Conversion Rate Optimizer', dept:'CRO Division',
    color:'#4488ff', hair:'#1a2a50', skin:'#6b4226', pants:'#1a2a4a', shoes:'#0a1a2a',
    schedule:'Wed 11:29 UTC', cronDays:[3], cronH:11, cronM:29,
    stateKeys:['cro'], deskTile:{x:25,y:12}, roomId:'cro',
    tasks:['Analyze Shopify funnel weekly','Design A/B test hypotheses','Review cart abandonment','Benchmark vs 3-5% CVR','Queue UX recommendations'],
    rules:['NEVER edit live store','Hypothesis + metric required','Data-driven only','Queue all changes'],
    apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Shopify GraphQL',icon:'🛍️',color:'#96bf48'}],
    dataFlow:{reads:['departments/cro/experiments.json','departments/cro/metrics.json','departments/intel/customer-language.json','config/niche.json'],writes:['departments/cro/experiments.json','departments/cro/audit-log.md'],feeds:['Queue (human approval)']},
  },
];

const X_INTEL = {
  id:'x_intel', name:'ECHO', fullName:'Echo Matsuda',
  title:'X Intelligence Analyst', dept:'X/Twitter Division',
  color:'#1DA1F2', hair:'#1a2030', skin:'#f0c8a0', pants:'#1a2a3a', shoes:'#0a1520',
  schedule:'Daily 7:00 UTC', cronDays:[0,1,2,3,4,5,6], cronH:7, cronM:0,
  stateKeys:['x_intel'], deskTile:{x:16,y:6}, roomId:'x_intel',
  tasks:['Monitor X for refurb phone conversations','Track competitor mentions & promotions','Capture customer sentiment & pain points','Spot trending topics & viral formats','Package intel for Content, Social, Email, SEO'],
  rules:['Never fabricate tweets or sources','Paraphrase if exact text unavailable','Tag which departments need each finding','Prioritize actionable intel over noise','Flag time-sensitive opportunities'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'X API v2',icon:'𝕏',color:'#1DA1F2'}],
  dataFlow:{reads:['departments/intel/trends.json','config/niche.json','config/competitors-list.json'],writes:['departments/x-intel/daily-brief.json'],feeds:['Content','Social','Email','SEO']},
};

const IMAGE_PROMPT = {
  id:'image_prompts', name:'LENS', fullName:'Lens Nakamura',
  title:'Visual Director / Image Prompter', dept:'Creative Division',
  color:'#e879f9', hair:'#2a1a2a', skin:'#c68642', pants:'#3a1a3a', shoes:'#1a0a1a',
  schedule:'Mon/Wed/Fri 8:19 UTC', cronDays:[1,3,5], cronH:8, cronM:19,
  stateKeys:['image_prompts'], deskTile:{x:12,y:12}, roomId:'cro',
  tasks:['Generate photorealistic image prompts for social posts','Product hero shots (Phase One IQ4, 100mm macro)','Lifestyle scenes (Canon R5, 85mm f/1.2, Portra 400)','Sustainability visuals (Leica M11, natural light)','Match prompts to campaign keywords & audience'],
  rules:['8-layer formula on every prompt','700-1000 chars max — short prompts win','Real camera + lens + film stock always','Skin realism stack on all people','Show real phone brands (iPhone, Samsung, Pixel)','Diverse people — vary age, ethnicity, gender','No text on images — overlays added later','Phone always looks pristine/like-new'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Image Gen',icon:'🎨',color:'#e879f9'}],
  dataFlow:{reads:['departments/social/calendar.json','departments/content/calendar.json','departments/x-intel/daily-brief.json','departments/seo/keywords.json'],writes:['departments/social/image-prompts.json'],feeds:['Social','Content','Email']},
};

const PROMPT_QA = {
  id:'prompt_qa', name:'FOCUS', fullName:'Focus Tanaka',
  title:'Prompt QA Inspector', dept:'Creative Division',
  color:'#f59e0b', hair:'#1a1a2a', skin:'#d4a574', pants:'#3a2a1a', shoes:'#1a0a0a',
  schedule:'Mon/Wed/Fri 8:49 UTC', cronDays:[1,3,5], cronH:8, cronM:49,
  stateKeys:['prompt_qa'], deskTile:{x:10,y:12}, roomId:'cro',
  tasks:['Run 15-check QA on every image prompt','Verify camera body + lens + film stock','Check skin realism stack on people shots','Validate phone models & correct colors','Score prompts: EXCELLENT / GOOD / NEEDS WORK / BLOCKED','Return failed prompts to LENS with fixes'],
  rules:['All 15 checks on every prompt — no shortcuts','Never approve without camera body, lens, or negative prompt','Be specific — line-level feedback, not vague','Always provide corrected prompt when fixes needed','Track recurring LENS issues and note patterns','Batch review: check diversity across full set'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'}],
  dataFlow:{reads:['departments/social/image-prompts.json','agents/custom/image-prompting-agent.md'],writes:['departments/social/image-prompts.json'],feeds:['Social','Content','Email']},
};

const BLOG_WRITER = {
  id:'blog_writer', name:'SCRIBE', fullName:'Scribe Delacroix',
  title:'Blog Writer', dept:'Content Division',
  color:'#10b981', hair:'#3a2a1a', skin:'#f0c8a0', pants:'#1a3a2a', shoes:'#0a1a0a',
  schedule:'Mon/Wed/Fri 9:30 UTC', cronDays:[1,3,5], cronH:9, cronM:30,
  stateKeys:['blog_writer'], deskTile:{x:23,y:5}, roomId:'content',
  tasks:['Read intel trends, SEO keywords, customer language','Write 1200-2000 word SEO-optimized blog posts','Internal links to products (iPhone, Galaxy, Pixel)','Structure: H1, meta desc, H2/H3, FAQ schema','Match brand voice — confident, anti-corporate','Pass blog to QUILL for anti-AI review'],
  rules:['Every blog targets specific SEO keywords','Use real customer language from intel','Specific numbers beat vague claims','One clear CTA per post','NO AI-generated copy tells','3+ internal product links minimum'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'}],
  dataFlow:{reads:['departments/intel/trends.json','departments/seo/keywords.json','departments/x-intel/daily-brief.json','departments/intel/customer-language.json'],writes:['departments/content/blog-pipeline.json'],feeds:['QUILL (QA)','PRESS (publish)']},
};

const BLOG_QA = {
  id:'blog_qa', name:'QUILL', fullName:'Quill Okafor',
  title:'Blog Copy Police', dept:'Content Division',
  color:'#ef4444', hair:'#1a1a1a', skin:'#8d5524', pants:'#2a1a1a', shoes:'#0a0505',
  schedule:'Mon/Wed/Fri 10:00 UTC', cronDays:[1,3,5], cronH:10, cronM:0,
  stateKeys:['blog_qa'], deskTile:{x:25,y:5}, roomId:'content',
  tasks:['Run 23-check anti-AI audit on every blog draft','Check banned words (60+) and phrases (40+)','Verify sentence rhythm variance & burstiness','Ensure brand voice — not corporate, not AI','Check SEO: title tags, meta desc, keyword density','Approve, reject, or block with specific fixes'],
  rules:['23 checks on EVERY blog — no exceptions','Zero banned words or it fails','Sentence length must vary 5-25 words','Must have contractions and conversational tone','EXCELLENT ships, NEEDS WORK returns to SCRIBE','BLOCKED = full rewrite required'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'}],
  dataFlow:{reads:['departments/content/blog-pipeline.json','config/copy-rules.json'],writes:['departments/content/blog-pipeline.json'],feeds:['PRESS (publish)','SCRIBE (fixes)']},
};

const BLOG_PUBLISHER = {
  id:'blog_publish', name:'PRESS', fullName:'Press Hawthorne',
  title:'Blog Publisher', dept:'Publishing Division',
  color:'#6366f1', hair:'#2a1a3a', skin:'#e0c8a0', pants:'#1a1a3a', shoes:'#0a0a1a',
  schedule:'Mon/Wed/Fri 10:30 UTC', cronDays:[1,3,5], cronH:10, cronM:30,
  stateKeys:['blog_publish'], deskTile:{x:30,y:12}, roomId:'cro',
  tasks:['Take QA-approved blogs from pipeline','Format HTML for Shopify Blog API','Add structured data (Article, FAQ, Breadcrumb)','Insert internal links to product pages','Add related products section','Queue for human approval before publishing'],
  rules:['NEVER auto-publish — always queue for approval','Every blog gets Article + FAQ schema','3+ internal product links required','Proper og:tags and SEO metadata','Image prompt reference for header','Shopify publish only after human approves'],
  apis:[{name:'Claude API',icon:'🧠',color:'#d97706'},{name:'Shopify API',icon:'🛍️',color:'#96bf48'}],
  dataFlow:{reads:['departments/content/blog-pipeline.json','departments/social/image-prompts.json'],writes:['departments/content/blog-pipeline.json','state/queue.json'],feeds:['You (approval queue)','Shopify (after approval)']},
};

const DIALER = {
  id:'dialer', name:'DIALER', fullName:'Dialer Voss',
  title:'Outbound Call Agent', dept:'Sales Division',
  color:'#16a34a', hair:'#2a1a0a', skin:'#c68642', pants:'#1a2a1a', shoes:'#0a0a0a',
  schedule:'Mon-Fri 14:15 UTC', cronDays:[1,2,3,4,5], cronH:14, cronM:15,
  stateKeys:['dialer'], deskTile:{x:30,y:5}, roomId:'content',
  tasks:['Scan Shopify for abandoned carts ($300+)','Identify 60-day inactive customers for win-back','Build prioritized call lists with reasons','Queue call lists for human approval','Execute approved calls via Vapi.ai','Log call outcomes and do-not-call requests'],
  rules:['NEVER make calls without approval','Max 20 calls per day','No calls on Sundays','Respect do-not-call permanently','One attempt per customer per week','Abandoned cart calls within 48hrs only'],
  apis:[{name:'Vapi.ai',icon:'📞',color:'#16a34a'},{name:'Shopify API',icon:'🛍️',color:'#96bf48'},{name:'Claude API',icon:'🧠',color:'#d97706'}],
  dataFlow:{reads:['Shopify abandoned carts','Shopify customer history','departments/dialer/call-list.json'],writes:['departments/dialer/call-list.json','state/queue.json'],feeds:['You (approval)','Vapi.ai (calls)']},
};

const TELEGRAM_BOT = {
  id:'telegram', name:'RELAY', fullName:'Relay Nakamura',
  title:'Telegram Comms Officer', dept:'Communications',
  color:'#0088cc', hair:'#1a2a3a', skin:'#d4a574', pants:'#1a1a2a', shoes:'#0a0a1a',
  schedule:'Every 5 min (polling)', cronDays:[0,1,2,3,4,5,6], cronH:0, cronM:0,
  stateKeys:['telegram'], deskTile:{x:18,y:1}, roomId:'lobby',
  tasks:['Poll Telegram for incoming commands','Route /status /queue /blog /approve commands','Send department completion notifications','Send error alerts immediately','Daily org summary at 7:00 UTC','Relay approval requests to owner'],
  rules:['Respond to ALL messages within 5 min','Send notification on every department run','Error alerts = highest priority','Never expose API keys in messages','Auto-discover chat ID on first /start','Queue approvals flow through Telegram'],
  apis:[{name:'Telegram Bot API',icon:'✈️',color:'#0088cc'}],
  dataFlow:{reads:['state/master.json','state/queue.json','departments/content/blog-pipeline.json','departments/social/image-prompts.json'],writes:['config/telegram.json','state/telegram_offset.json','state/queue.json'],feeds:['You (Telegram)','All departments (notifications)']},
};

const GM = {
  id:'gm', name:'BOSS', fullName:'Boss Morgan',
  title:'General Manager / Enforcer', dept:'Executive',
  color:'#aa66ff', hair:'#222', skin:'#e0ac69', pants:'#2a1a3a', shoes:'#1a0a2a',
  schedule:'Daily 18:51 + Fri 7:03 UTC', cronDays:[0,1,2,3,4,5,6], cronH:18, cronM:51,
  stateKeys:['gm_report','gm_queue'], deskTile:{x:28,y:19}, roomId:'gm',
  tasks:['Friday: weekly report (Opus)','Daily: process queue','Monitor dept health','Flag overdue depts','Enforce all safety rules'],
  rules:['Emails NEVER auto-send','Shopify writes need approval','23-check on ALL copy','CRO = read-only','Git trail on everything','Idle past schedule = investigate'],
  apis:[{name:'Claude Opus',icon:'🧠',color:'#d97706'},{name:'All Dept Data',icon:'📊',color:'#a855f7'}],
  dataFlow:{reads:['state/master.json','state/queue.json','ALL department outputs'],writes:['departments/gm/weekly-report.md','state/queue.json'],feeds:['You (weekly report)']},
};

const ALL_CHARS = [...EMPLOYEES, X_INTEL, IMAGE_PROMPT, PROMPT_QA, BLOG_WRITER, BLOG_QA, BLOG_PUBLISHER, DIALER, TELEGRAM_BOT, GM];

// ═══════════════════════════════════════════
// POINTS OF INTEREST (where chars go for life sim)
// ═══════════════════════════════════════════
const POI = {
  coffee:   {x:2, y:18},
  cooler:   {x:4, y:18},
  printer:  {x:17,y:8},
  meeting:  {x:14,y:12},
  couch1:   {x:8, y:19},
  couch2:   {x:8, y:20},
  vending:  {x:18,y:18},
  lobby:    {x:17,y:2},
};

// ═══════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════
let masterState = null, queueState = null;
let canvas, ctx;
let selectedEmployee = null, hoveredEmployee = null;
let frame = 0;
let enforcerLog = [];

// Per-character state
const chars = {};
function initChars() {
  for (const c of ALL_CHARS) {
    chars[c.id] = {
      x: c.deskTile.x * T + T/2,
      y: c.deskTile.y * T + T/2,
      tx: c.deskTile.x * T + T/2,
      ty: c.deskTile.y * T + T/2,
      path: [],
      action: 'sitting',   // sitting, walking, typing, coffee, chatting, meeting
      actionTimer: 0,
      facing: 'down',      // up, down, left, right
      walkFrame: 0,
      bubble: null,         // speech/thought bubble text
      bubbleTimer: 0,
    };
  }
}

// ═══════════════════════════════════════════
// PATHFINDING (simple BFS on tile grid)
// ═══════════════════════════════════════════
function isWalkable(col, row) {
  if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return false;
  return MAP[row][col] !== 1;
}

function findPath(sx, sy, ex, ey) {
  const sc = Math.floor(sx / T), sr = Math.floor(sy / T);
  const ec = Math.floor(ex / T), er = Math.floor(ey / T);
  if (sc === ec && sr === er) return [];
  if (!isWalkable(ec, er)) return [];

  const visited = new Set();
  const queue = [[sc, sr, []]];
  visited.add(`${sc},${sr}`);

  while (queue.length > 0) {
    const [cx, cy, path] = queue.shift();
    const dirs = [[0,-1],[0,1],[-1,0],[1,0]];
    for (const [dx, dy] of dirs) {
      const nx = cx+dx, ny = cy+dy;
      const key = `${nx},${ny}`;
      if (!visited.has(key) && isWalkable(nx, ny)) {
        const newPath = [...path, {x: nx*T + T/2, y: ny*T + T/2}];
        if (nx === ec && ny === er) return newPath;
        visited.add(key);
        queue.push([nx, ny, newPath]);
      }
    }
  }
  return [];
}

function sendCharTo(id, tx, ty) {
  const c = chars[id];
  const path = findPath(c.x, c.y, tx, ty);
  if (path.length > 0) {
    c.path = path;
    c.action = 'walking';
  }
}

// ═══════════════════════════════════════════
// CHARACTER AI — life sim behaviors
// ═══════════════════════════════════════════
function updateCharAI() {
  for (const emp of ALL_CHARS) {
    const c = chars[emp.id];
    const status = getDeptStatus(emp.id);

    // Decrease timers
    if (c.actionTimer > 0) { c.actionTimer--; continue; }
    if (c.bubbleTimer > 0) { c.bubbleTimer--; } else { c.bubble = null; }

    // If walking, don't change action
    if (c.action === 'walking' && c.path.length > 0) continue;

    // Choose next action based on status
    const roll = Math.random();

    if (status === 'working' || status === 'ok') {
      // Productive employee — mostly at desk typing, occasionally coffee/printer
      if (roll < 0.65) {
        // Go to desk and type
        goToDesk(emp);
        c.action = 'typing';
        c.actionTimer = 200 + Math.random() * 300;
        if (Math.random() < 0.3) {
          const xBubbles = ['scanning X...','trending now...','competitor spotted!','new thread...'];
          c.bubble = status === 'working' ?
            (emp.id === 'x_intel' ? pickRandom(xBubbles) : pickRandom(['coding...','analyzing...','crunching data...','writing report...'])) :
            (emp.id === 'x_intel' ? pickRandom(['X is quiet...','checking feeds...']) : pickRandom(['done!','reviewing...','checking logs...']));
          c.bubbleTimer = 120;
        }
      } else if (roll < 0.80) {
        // Coffee break
        sendCharTo(emp.id, POI.coffee.x * T + T/2, POI.coffee.y * T + T/2);
        c.actionTimer = 150;
        c.bubble = pickRandom(['need coffee','caffeine time','brb coffee']);
        c.bubbleTimer = 80;
      } else if (roll < 0.90) {
        // Water cooler
        sendCharTo(emp.id, POI.cooler.x * T + T/2, POI.cooler.y * T + T/2);
        c.actionTimer = 120;
        c.bubble = 'hydrating';
        c.bubbleTimer = 60;
      } else {
        // Printer run
        sendCharTo(emp.id, POI.printer.x * T + T/2, POI.printer.y * T + T/2);
        c.actionTimer = 100;
        c.bubble = 'printing...';
        c.bubbleTimer = 60;
      }
    } else if (status === 'idle') {
      // Idle employee — wanders, checks phone, gets coffee a lot
      if (roll < 0.30) {
        goToDesk(emp);
        c.action = 'sitting';
        c.actionTimer = 100 + Math.random() * 200;
        if (Math.random() < 0.4) {
          c.bubble = pickRandom(['...','*scrolling*','waiting...','nothing to do','*yawn*']);
          c.bubbleTimer = 100;
        }
      } else if (roll < 0.50) {
        // Wander in room
        const room = ROOMS.find(r => r.id === emp.roomId);
        if (room) {
          const rx = (room.x + 1 + Math.random() * (room.w - 2)) * T + T/2;
          const ry = (room.y + 1 + Math.random() * (room.h - 2)) * T + T/2;
          sendCharTo(emp.id, rx, ry);
          c.actionTimer = 80;
        }
      } else if (roll < 0.65) {
        sendCharTo(emp.id, POI.coffee.x * T + T/2, POI.coffee.y * T + T/2);
        c.actionTimer = 150;
        c.bubble = pickRandom(["3rd coffee...","bored","again?"]);
        c.bubbleTimer = 80;
      } else if (roll < 0.80) {
        sendCharTo(emp.id, POI.cooler.x * T + T/2, POI.cooler.y * T + T/2);
        c.actionTimer = 130;
      } else {
        // Couch in break room
        const couch = Math.random() < 0.5 ? POI.couch1 : POI.couch2;
        sendCharTo(emp.id, couch.x * T + T/2, couch.y * T + T/2);
        c.actionTimer = 200;
        c.bubble = pickRandom(['*stretching*','break time','*resting*']);
        c.bubbleTimer = 80;
      }
    } else if (status === 'error') {
      // Stressed, pacing
      if (roll < 0.4) {
        goToDesk(emp);
        c.action = 'typing';
        c.actionTimer = 60;
        c.bubble = pickRandom(['ERROR!','oh no','fixing...','help!']);
        c.bubbleTimer = 100;
      } else {
        // Pace around room
        const room = ROOMS.find(r => r.id === emp.roomId);
        if (room) {
          const rx = (room.x + 1 + Math.random() * (room.w - 2)) * T + T/2;
          const ry = (room.y + 1 + Math.random() * (room.h - 2)) * T + T/2;
          sendCharTo(emp.id, rx, ry);
          c.actionTimer = 40;
          c.bubble = '!!!';
          c.bubbleTimer = 40;
        }
      }
    }
  }

  // GM special: patrol behavior
  gmPatrolAI();
}

function goToDesk(emp) {
  sendCharTo(emp.id, emp.deskTile.x * T + T/2, emp.deskTile.y * T + T/2);
}

function gmPatrolAI() {
  const gm = chars['gm'];
  if (gm.action === 'walking' && gm.path.length > 0) return;
  if (gm.actionTimer > 0) return;

  // Check for idle employees to visit
  const allStaff = [...EMPLOYEES, X_INTEL, IMAGE_PROMPT, PROMPT_QA, BLOG_WRITER, BLOG_QA, BLOG_PUBLISHER];
  for (const emp of allStaff) {
    const status = getDeptStatus(emp.id);
    if (status === 'idle' || status === 'error') {
      const shouldVisit = Math.random() < 0.15;
      if (shouldVisit) {
        // Walk to their room door
        const room = ROOMS.find(r => r.id === emp.roomId);
        if (room) {
          sendCharTo('gm', room.doorX * T + T/2, room.doorY * T + T/2);
          gm.actionTimer = 200;
          gm.bubble = status === 'error' ? `${emp.name}! Report!` : `${emp.name}, status?`;
          gm.bubbleTimer = 120;

          const type = status === 'error' ? 'alert' : 'warn';
          addEnforcerLog(type, `Visiting ${emp.name} — ${status.toUpperCase()}`);
          return;
        }
      }
    }
  }
}

// ═══════════════════════════════════════════
// MOVEMENT
// ═══════════════════════════════════════════
const WALK_SPEED = 2.0;

function updateMovement() {
  for (const emp of ALL_CHARS) {
    const c = chars[emp.id];
    if (c.path.length === 0) {
      if (c.action === 'walking') c.action = 'sitting';
      c.walkFrame = 0;
      continue;
    }

    const next = c.path[0];
    const dx = next.x - c.x;
    const dy = next.y - c.y;
    const dist = Math.sqrt(dx*dx + dy*dy);

    if (dist < WALK_SPEED + 1) {
      c.x = next.x;
      c.y = next.y;
      c.path.shift();
    } else {
      c.x += (dx/dist) * WALK_SPEED;
      c.y += (dy/dist) * WALK_SPEED;
    }

    // Facing direction
    if (Math.abs(dx) > Math.abs(dy)) {
      c.facing = dx > 0 ? 'right' : 'left';
    } else {
      c.facing = dy > 0 ? 'down' : 'up';
    }

    c.walkFrame++;
    c.action = 'walking';
  }
}

// ═══════════════════════════════════════════
// DRAWING
// ═══════════════════════════════════════════
function draw() {
  ctx.clearRect(0, 0, W, H);

  drawFloor();
  drawWalls();
  drawRoomLabels();
  drawFurniture();
  drawCharacters();
  drawHoverHighlight();
}

function drawFloor() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = MAP[r][c];
      if (tile === 0 || tile === 2) {
        // Checkerboard floor
        ctx.fillStyle = (c + r) % 2 === 0 ? '#16162e' : '#181838';
        ctx.fillRect(c*T, r*T, T, T);
      }
    }
  }

  // Room floor tints
  for (const room of ROOMS) {
    ctx.fillStyle = room.color + '08';
    ctx.fillRect(room.x*T, room.y*T, room.w*T, room.h*T);
  }

  // Break room floor
  ctx.fillStyle = '#1a1a2e';
  ctx.fillRect(BREAKROOM.x*T, BREAKROOM.y*T, BREAKROOM.w*T, BREAKROOM.h*T);

  // Meeting room floor
  ctx.fillStyle = '#181830';
  ctx.fillRect(MEETING.x*T, MEETING.y*T, MEETING.w*T, MEETING.h*T);

  // Lobby carpet strip
  ctx.fillStyle = '#201828';
  ctx.fillRect(T*5, T*1, T*25, T*2);
}

function drawWalls() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = MAP[r][c];
      if (tile === 1) {
        // Wall base
        ctx.fillStyle = '#282850';
        ctx.fillRect(c*T, r*T, T, T);
        // Wall top highlight
        ctx.fillStyle = '#323268';
        ctx.fillRect(c*T, r*T, T, 4);
        // Wall bottom shadow
        ctx.fillStyle = '#1a1a3a';
        ctx.fillRect(c*T, r*T+T-3, T, 3);
        // Subtle brick pattern
        if ((c+r) % 3 === 0) {
          ctx.fillStyle = '#2e2e58';
          ctx.fillRect(c*T+2, r*T+8, T-4, 2);
        }
        if ((c+r) % 3 === 1) {
          ctx.fillStyle = '#2e2e58';
          ctx.fillRect(c*T+6, r*T+18, T-8, 2);
        }
      } else if (tile === 2) {
        // Door
        ctx.fillStyle = '#16162e';
        ctx.fillRect(c*T, r*T, T, T);
        // Door frame
        ctx.fillStyle = '#4a4a3a';
        ctx.fillRect(c*T, r*T, 3, T);
        ctx.fillRect(c*T+T-3, r*T, 3, T);
        ctx.fillRect(c*T, r*T, T, 3);
        // Door mat
        ctx.fillStyle = '#3a3a2a';
        ctx.fillRect(c*T+4, r*T+T-6, T-8, 4);
      }
    }
  }
}

function drawRoomLabels() {
  ctx.font = '7px "Press Start 2P"';
  ctx.textAlign = 'center';

  for (const room of ROOMS) {
    const status = getDeptStatus(room.id);
    // Room name plate on wall
    const cx = (room.x + room.w/2) * T;
    const cy = room.y * T + 10;

    // Name plate background
    ctx.fillStyle = '#1a1a3a';
    const tw = ctx.measureText(room.label).width + 12;
    ctx.fillRect(cx - tw/2, cy - 8, tw, 12);

    // Status-tinted text
    ctx.fillStyle = status === 'working' ? room.color :
                    status === 'ok' ? room.color + 'aa' :
                    status === 'error' ? '#ff4466' : '#555';
    ctx.fillText(room.label, cx, cy);

    // Status LED
    const ledX = (room.x + room.w - 1) * T + T - 6;
    const ledY = room.y * T + 6;
    ctx.beginPath();
    ctx.arc(ledX, ledY, 4, 0, Math.PI*2);
    ctx.fillStyle = status === 'working' ? '#0f8' :
                    status === 'ok' ? '#0f8' :
                    status === 'error' ? '#f46' : '#333';
    if (status === 'working') {
      ctx.shadowColor = '#0f8'; ctx.shadowBlur = 10;
    }
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // Special area labels
  ctx.fillStyle = '#444';
  ctx.fillText('RECEPTION', LOBBY.x*T + LOBBY.w*T/2, LOBBY.y*T + 10);
  ctx.fillText('BREAK ROOM', BREAKROOM.x*T + BREAKROOM.w*T/2, BREAKROOM.y*T + 10);
  ctx.fillText('MEETING ROOM', MEETING.x*T + MEETING.w*T/2, MEETING.y*T + 10);

  ctx.textAlign = 'left';
}

function drawFurniture() {
  for (const f of FURNITURE) {
    const x = f.x * T, y = f.y * T;
    switch (f.type) {
      case 'desk':
        // L-shaped desk
        ctx.fillStyle = '#3a3024';
        ctx.fillRect(x, y, T*1.5, T*0.8);
        ctx.fillRect(x, y, T*0.4, T*1.2);
        // Desk edge highlight
        ctx.fillStyle = '#4a4034';
        ctx.fillRect(x, y, T*1.5, 2);
        break;

      case 'desk_large':
        ctx.fillStyle = '#4a3a28';
        ctx.fillRect(x, y, (f.w||2)*T, T);
        ctx.fillStyle = '#5a4a38';
        ctx.fillRect(x, y, (f.w||2)*T, 3);
        break;

      case 'monitor':
        const sc = f.screen;
        const colors = {cyan:'#00ccff',green:'#00ff88',orange:'#ff8844',yellow:'#ffcc00',pink:'#ff66aa',blue:'#4488ff',purple:'#aa66ff',xblue:'#1DA1F2'};
        const status = getDeptStatusByPos(f.x, f.y);
        // Monitor stand
        ctx.fillStyle = '#2a2a3a';
        ctx.fillRect(x+T*0.5, y-T*0.1, T*0.4, T*0.15);
        // Screen
        ctx.fillStyle = status === 'working' ? (colors[sc]||'#0cf') :
                        status === 'ok' ? '#1a3a2a' : '#111';
        ctx.fillRect(x+T*0.1, y-T*0.6, T*1.2, T*0.55);
        // Screen border
        ctx.strokeStyle = '#3a3a4a';
        ctx.lineWidth = 1;
        ctx.strokeRect(x+T*0.1, y-T*0.6, T*1.2, T*0.55);
        // Screen glow if working
        if (status === 'working') {
          const pulse = Math.sin(frame * 0.03) * 0.15 + 0.85;
          ctx.fillStyle = (colors[sc]||'#0cf') + Math.floor(pulse*30).toString(16).padStart(2,'0');
          ctx.fillRect(x+T*0.15, y-T*0.55, T*1.1, T*0.45);
          // Text lines on screen
          ctx.fillStyle = '#fff3';
          for (let i = 0; i < 3; i++) {
            ctx.fillRect(x+T*0.2, y-T*0.5+i*5, T*(0.4+Math.random()*0.5), 2);
          }
        }
        break;

      case 'chair':
        ctx.fillStyle = '#2a2a44';
        ctx.fillRect(x+4, y+4, T-8, T-8);
        break;

      case 'bookshelf':
        ctx.fillStyle = '#3a2a1a';
        ctx.fillRect(x+2, y+2, T-4, T-4);
        // Books
        const bookColors = ['#a33','#3a3','#33a','#a83','#8a3'];
        for (let i = 0; i < 4; i++) {
          ctx.fillStyle = bookColors[i % bookColors.length];
          ctx.fillRect(x+4+i*6, y+4, 5, T-10);
        }
        // Shelf lines
        ctx.fillStyle = '#4a3a2a';
        ctx.fillRect(x+2, y+T/2, T-4, 2);
        break;

      case 'plant':
        // Pot
        ctx.fillStyle = '#5a3a2a';
        ctx.fillRect(x+8, y+16, 16, 12);
        ctx.fillRect(x+6, y+14, 20, 4);
        // Leaves
        ctx.fillStyle = '#2a6a3a';
        ctx.beginPath();
        ctx.ellipse(x+16, y+10, 10, 8, 0, 0, Math.PI*2);
        ctx.fill();
        ctx.fillStyle = '#3a8a4a';
        ctx.beginPath();
        ctx.ellipse(x+12, y+8, 6, 5, -0.3, 0, Math.PI*2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(x+20, y+8, 6, 5, 0.3, 0, Math.PI*2);
        ctx.fill();
        break;

      case 'coffee':
        // Coffee machine
        ctx.fillStyle = '#2a2a3a';
        ctx.fillRect(x+4, y+4, T-8, T-4);
        ctx.fillStyle = '#4a2a1a';
        ctx.fillRect(x+6, y+6, T-12, T/2-4);
        // Red indicator light
        ctx.fillStyle = '#f44';
        ctx.fillRect(x+T-10, y+6, 4, 4);
        // "COFFEE" label
        ctx.fillStyle = '#666';
        ctx.font = '4px "Press Start 2P"';
        ctx.fillText('COFFEE', x+5, y+T-4);
        break;

      case 'cooler':
        // Water cooler
        ctx.fillStyle = '#aaccee';
        ctx.fillRect(x+8, y+2, 16, 14);
        ctx.fillStyle = '#88aacc';
        ctx.fillRect(x+10, y+4, 12, 10);
        // Base
        ctx.fillStyle = '#3a3a4a';
        ctx.fillRect(x+6, y+16, 20, 12);
        // Tap
        ctx.fillStyle = '#6af';
        ctx.fillRect(x+14, y+16, 4, 4);
        break;

      case 'couch':
        const cw = (f.w || 2) * T;
        ctx.fillStyle = '#3a2a4a';
        ctx.fillRect(x+2, y+4, cw-4, T-6);
        // Cushions
        ctx.fillStyle = '#4a3a5a';
        ctx.fillRect(x+4, y+6, cw/2-6, T-10);
        ctx.fillRect(x+cw/2+2, y+6, cw/2-6, T-10);
        // Back
        ctx.fillStyle = '#2a1a3a';
        ctx.fillRect(x+2, y+2, cw-4, 6);
        break;

      case 'table':
        ctx.fillStyle = '#3a3028';
        ctx.fillRect(x+4, y+4, (f.w||1)*T-8, (f.h||1)*T-8);
        ctx.fillStyle = '#4a4038';
        ctx.fillRect(x+4, y+4, (f.w||1)*T-8, 3);
        break;

      case 'conf_table':
        // Long conference table
        const tw2 = (f.w||4)*T, th = (f.h||2)*T;
        ctx.fillStyle = '#3a3028';
        ctx.fillRect(x+4, y+4, tw2-8, th-8);
        ctx.fillStyle = '#4a4038';
        ctx.fillRect(x+4, y+4, tw2-8, 3);
        // Chairs around table
        ctx.fillStyle = '#2a2a44';
        for (let i = 0; i < f.w; i++) {
          ctx.fillRect(x+i*T+8, y-6, 16, 8);  // top chairs
          ctx.fillRect(x+i*T+8, y+th-2, 16, 8); // bottom chairs
        }
        break;

      case 'whiteboard':
        ctx.fillStyle = '#dde';
        ctx.fillRect(x+2, y+4, (f.w||2)*T-4, T*0.7);
        ctx.strokeStyle = '#99a';
        ctx.lineWidth = 2;
        ctx.strokeRect(x+2, y+4, (f.w||2)*T-4, T*0.7);
        // Scribbles
        ctx.strokeStyle = '#33a3';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x+10, y+10); ctx.lineTo(x+40, y+15);
        ctx.moveTo(x+10, y+18); ctx.lineTo(x+50, y+20);
        ctx.moveTo(x+10, y+24); ctx.lineTo(x+35, y+22);
        ctx.stroke();
        break;

      case 'board':
        ctx.fillStyle = '#2a3a2a';
        ctx.fillRect(x, y+4, (f.w||2)*T, T*0.7);
        ctx.fillStyle = '#4a6a4a';
        ctx.font = '6px "Press Start 2P"';
        ctx.fillText(f.text||'', x+4, y+18);
        break;

      case 'vending':
        ctx.fillStyle = '#2a3a4a';
        ctx.fillRect(x+4, y+2, T-8, T-2);
        ctx.fillStyle = '#1a2a3a';
        ctx.fillRect(x+6, y+4, T-12, T/2);
        // Colored items
        ctx.fillStyle = '#e44'; ctx.fillRect(x+8, y+6, 5, 5);
        ctx.fillStyle = '#4e4'; ctx.fillRect(x+15, y+6, 5, 5);
        ctx.fillStyle = '#44e'; ctx.fillRect(x+8, y+13, 5, 5);
        ctx.fillStyle = '#ee4'; ctx.fillRect(x+15, y+13, 5, 5);
        break;

      case 'printer':
        ctx.fillStyle = '#3a3a4a';
        ctx.fillRect(x+4, y+8, T-8, T-12);
        ctx.fillStyle = '#4a4a5a';
        ctx.fillRect(x+2, y+6, T-4, 6);
        // Paper tray
        ctx.fillStyle = '#ddd';
        ctx.fillRect(x+8, y+T-6, T-16, 4);
        break;

      case 'reception_desk':
        const rw = (f.w||3)*T;
        ctx.fillStyle = '#3a3028';
        ctx.fillRect(x, y+T*0.3, rw, T*0.7);
        ctx.fillStyle = '#4a4038';
        ctx.fillRect(x, y+T*0.3, rw, 4);
        // Front panel
        ctx.fillStyle = '#2a2018';
        ctx.fillRect(x+2, y+T*0.5, rw-4, T*0.4);
        // Company nameplate
        ctx.fillStyle = '#0f8';
        ctx.font = '5px "Press Start 2P"';
        ctx.fillText('GADGETGEEKS', x+rw/2-35, y+T*0.8);
        break;

      case 'sign':
        ctx.fillStyle = '#0f84';
        ctx.font = '10px "Press Start 2P"';
        ctx.textAlign = 'center';
        ctx.fillText(f.text, x, y+T*0.7);
        ctx.textAlign = 'left';
        break;
    }
  }
}

function getDeptStatusByPos(fx, fy) {
  for (const room of ROOMS) {
    if (fx >= room.x && fx < room.x+room.w && fy >= room.y && fy < room.y+room.h) {
      return getDeptStatus(room.id);
    }
  }
  return 'idle';
}

function drawCharacters() {
  // Sort by Y for proper overlapping
  const sorted = [...ALL_CHARS].sort((a,b) => chars[a.id].y - chars[b.id].y);

  for (const emp of sorted) {
    const c = chars[emp.id];
    const x = Math.round(c.x) - T/2;
    const y = Math.round(c.y) - T/2;
    const isWalking = c.action === 'walking';
    const isTyping = c.action === 'typing';

    // Walking bounce
    const bounce = isWalking ? Math.sin(c.walkFrame * 0.4) * 2 : 0;
    // Idle bob
    const bob = !isWalking ? Math.sin(frame * 0.015 + emp.id.length) * 0.8 : 0;
    const cy = y + bounce + bob;

    // Shadow
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.beginPath();
    ctx.ellipse(x+T/2, y+T+2, 9, 3, 0, 0, Math.PI*2);
    ctx.fill();

    // === CHARACTER BODY (16x32 style pixel character) ===

    // Hair
    ctx.fillStyle = emp.hair;
    ctx.fillRect(x+9, cy, 14, 6);

    // Head
    ctx.fillStyle = emp.skin;
    ctx.fillRect(x+10, cy+3, 12, 12);

    // Eyes
    const blink = frame % 300 > 295;
    ctx.fillStyle = '#111';
    if (blink) {
      ctx.fillRect(x+13, cy+8, 3, 1);
      ctx.fillRect(x+18, cy+8, 3, 1);
    } else {
      // Eyes face direction
      const ex = c.facing === 'left' ? -1 : c.facing === 'right' ? 1 : 0;
      ctx.fillRect(x+13, cy+7, 3, 3);
      ctx.fillRect(x+18, cy+7, 3, 3);
      ctx.fillStyle = '#fff';
      ctx.fillRect(x+14+ex, cy+7, 1, 1);
      ctx.fillRect(x+19+ex, cy+7, 1, 1);
    }

    // Mouth (tiny)
    ctx.fillStyle = emp.skin === '#6b4226' || emp.skin === '#8d5524' ? '#5a3a1a' : '#c08060';
    ctx.fillRect(x+14, cy+12, 4, 1);

    // Shirt / body
    ctx.fillStyle = emp.color;
    ctx.fillRect(x+8, cy+15, 16, 11);
    // Collar
    ctx.fillStyle = lightenColor(emp.color, 1.2);
    ctx.fillRect(x+12, cy+15, 8, 2);
    // Arms
    ctx.fillStyle = emp.color;
    if (isTyping) {
      // Arms forward (typing)
      ctx.fillRect(x+4, cy+17, 5, 6);
      ctx.fillRect(x+23, cy+17, 5, 6);
      // Hands
      ctx.fillStyle = emp.skin;
      ctx.fillRect(x+4, cy+22, 4, 3);
      ctx.fillRect(x+24, cy+22, 4, 3);
    } else if (isWalking) {
      const armSwing = Math.sin(c.walkFrame * 0.4) * 3;
      ctx.fillRect(x+4, cy+16+armSwing, 5, 8);
      ctx.fillRect(x+23, cy+16-armSwing, 5, 8);
    } else {
      ctx.fillRect(x+4, cy+16, 5, 9);
      ctx.fillRect(x+23, cy+16, 5, 9);
    }

    // Pants
    ctx.fillStyle = emp.pants;
    ctx.fillRect(x+9, cy+26, 6, 4);
    ctx.fillRect(x+17, cy+26, 6, 4);

    // Legs + shoes
    ctx.fillStyle = emp.pants;
    if (isWalking) {
      const legSwing = Math.sin(c.walkFrame * 0.4);
      ctx.fillRect(x+10, cy+30, 5, 4 + legSwing*2);
      ctx.fillRect(x+17, cy+30, 5, 4 - legSwing*2);
    } else {
      ctx.fillRect(x+10, cy+30, 5, 4);
      ctx.fillRect(x+17, cy+30, 5, 4);
    }
    // Shoes
    ctx.fillStyle = emp.shoes;
    const shoeY = isWalking ? cy+33+Math.abs(Math.sin(c.walkFrame*0.4)) : cy+33;
    ctx.fillRect(x+9, shoeY, 6, 3);
    ctx.fillRect(x+17, shoeY, 6, 3);

    // === GM BADGE ===
    if (emp.id === 'gm') {
      ctx.fillStyle = '#aa66ff';
      ctx.fillRect(x+20, cy+16, 8, 8);
      ctx.fillStyle = '#fff';
      ctx.font = '6px "Press Start 2P"';
      ctx.fillText('GM', x+20, cy+23);
    }

    // === NAME TAG ===
    ctx.font = '6px "Press Start 2P"';
    ctx.textAlign = 'center';
    const nw = ctx.measureText(emp.name).width + 8;
    ctx.fillStyle = 'rgba(0,0,0,0.75)';
    ctx.fillRect(x+T/2-nw/2, cy-10, nw, 10);
    ctx.fillStyle = emp.color;
    ctx.fillText(emp.name, x+T/2, cy-2);
    ctx.textAlign = 'left';

    // === STATUS ICON ===
    const status = getDeptStatus(emp.id);
    ctx.textAlign = 'center';
    if (status === 'working' && !isWalking) {
      const gears = ['|','/','-','\\'];
      ctx.fillStyle = '#0f8';
      ctx.font = '8px "Press Start 2P"';
      ctx.fillText(gears[Math.floor(frame*0.08)%4], x+T/2, cy-14);
    } else if (status === 'idle') {
      if (frame % 150 < 100) {
        ctx.fillStyle = '#5558';
        ctx.font = '5px "Press Start 2P"';
        const zPhase = Math.floor(frame/30) % 3;
        ctx.fillText('z'.repeat(zPhase+1), x+T/2+6, cy-14-(frame%150)*0.05);
      }
    } else if (status === 'error') {
      if (frame % 50 < 35) {
        ctx.fillStyle = '#f46';
        ctx.font = '9px "Press Start 2P"';
        ctx.fillText('!', x+T/2, cy-14);
      }
    }
    ctx.textAlign = 'left';

    // === SPEECH BUBBLE ===
    if (c.bubble && c.bubbleTimer > 0) {
      drawBubble(x + T/2, cy - 22, c.bubble);
    }
  }
}

function drawBubble(x, y, text) {
  ctx.font = '5px "Press Start 2P"';
  const tw = ctx.measureText(text).width + 10;
  const bx = x - tw/2;
  const by = y - 14;

  // Bubble background
  ctx.fillStyle = '#fff';
  ctx.fillRect(bx, by, tw, 12);
  // Bubble border
  ctx.strokeStyle = '#333';
  ctx.lineWidth = 1;
  ctx.strokeRect(bx, by, tw, 12);
  // Pointer triangle
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.moveTo(x-3, by+12);
  ctx.lineTo(x+3, by+12);
  ctx.lineTo(x, by+16);
  ctx.fill();
  // Text
  ctx.fillStyle = '#222';
  ctx.textAlign = 'center';
  ctx.fillText(text, x, by+9);
  ctx.textAlign = 'left';
}

function drawHoverHighlight() {
  if (!hoveredEmployee) return;
  const c = chars[hoveredEmployee.id];
  const x = Math.round(c.x) - T/2;
  const y = Math.round(c.y) - T/2;
  ctx.strokeStyle = '#fff8';
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 4]);
  ctx.strokeRect(x-2, y-14, T+4, T+20);
  ctx.setLineDash([]);
}

// ═══════════════════════════════════════════
// GAME LOOP
// ═══════════════════════════════════════════
function gameLoop() {
  frame++;
  updateMovement();
  if (frame % 8 === 0) updateCharAI();
  draw();
  requestAnimationFrame(gameLoop);
}

// ═══════════════════════════════════════════
// INTERACTION
// ═══════════════════════════════════════════
function onMouseMove(e) {
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width / rect.width, sy = canvas.height / rect.height;
  const mx = (e.clientX - rect.left) * sx;
  const my = (e.clientY - rect.top) * sy;

  hoveredEmployee = null;
  const tip = document.getElementById('tooltip');

  for (const emp of ALL_CHARS) {
    const c = chars[emp.id];
    const ex = c.x - T/2, ey = c.y - T/2;
    if (mx >= ex-4 && mx <= ex+T+4 && my >= ey-14 && my <= ey+T+8) {
      hoveredEmployee = emp;
      const status = getDeptStatus(emp.id);
      const action = c.action;
      tip.innerHTML = `<b style="color:${emp.color}">${emp.fullName}</b> (${emp.name})<br>` +
        `${emp.title}<br>` +
        `Status: <span style="color:${status==='ok'||status==='working'?'#0f8':status==='error'?'#f46':'#667'}">${status.toUpperCase()}</span> ` +
        `| ${action}`;
      tip.classList.remove('hidden');
      tip.style.left = Math.min(e.clientX - rect.left + 16, rect.width - 250) + 'px';
      tip.style.top = (e.clientY - rect.top - 10) + 'px';
      canvas.style.cursor = 'pointer';
      return;
    }
  }
  tip.classList.add('hidden');
  canvas.style.cursor = 'crosshair';
}

function onClick(e) {
  if (hoveredEmployee) selectEmployee(hoveredEmployee);
}

// ═══════════════════════════════════════════
// SIDEBAR
// ═══════════════════════════════════════════
function selectEmployee(emp) {
  selectedEmployee = emp;
  document.querySelectorAll('.dir-entry').forEach(el => el.classList.remove('selected'));
  const el = document.querySelector(`.dir-entry[data-id="${emp.id}"]`);
  if (el) el.classList.add('selected');
  document.getElementById('directory-section').classList.add('hidden');
  document.getElementById('employee-detail').classList.remove('hidden');
  renderEmployeeCard(emp);
}

function renderEmployeeCard(emp) {
  const card = document.getElementById('employee-card');
  const status = getDeptStatus(emp.id);
  const lastRun = getLastRun(emp.id);
  const totalRuns = getTotalRuns(emp.id);
  const nextRun = getNextRun(emp);
  const c = chars[emp.id];

  card.innerHTML = `
    <div class="emp-header">
      <canvas class="emp-avatar-lg" width="48" height="48" id="avatar-canvas"></canvas>
      <div>
        <div class="emp-name">${emp.fullName}</div>
        <div class="emp-title">${emp.title}</div>
        <div style="color:${emp.color};font-size:7px;margin-top:2px">${emp.dept}</div>
      </div>
    </div>
    <div class="emp-stats">
      <div class="emp-stat">
        <span class="emp-stat-label">STATUS</span>
        <span class="emp-stat-val" style="color:${status==='ok'||status==='working'?'#0f8':status==='error'?'#f46':'#667'}">${status.toUpperCase()}</span>
      </div>
      <div class="emp-stat">
        <span class="emp-stat-label">DOING</span>
        <span class="emp-stat-val">${c.action.toUpperCase()}</span>
      </div>
      <div class="emp-stat">
        <span class="emp-stat-label">RUNS</span>
        <span class="emp-stat-val">${totalRuns}</span>
      </div>
      <div class="emp-stat">
        <span class="emp-stat-label">LAST RUN</span>
        <span class="emp-stat-val">${timeAgo(lastRun)}</span>
      </div>
    </div>
    <div class="emp-section-title">NEXT RUN</div>
    <div class="emp-task" style="color:#fc0">${nextRun || 'Not scheduled today'}</div>
    <div class="emp-section-title">SCHEDULE</div>
    <div class="emp-task">${emp.schedule}</div>
    ${emp.apis ? `<div class="emp-section-title">API CONNECTIONS</div>
    <div class="emp-apis">${emp.apis.map(a => `<div class="emp-api-badge" style="border-color:${a.color}"><span class="api-icon">${a.icon}</span><span class="api-name" style="color:${a.color}">${a.name}</span></div>`).join('')}</div>` : ''}
    ${emp.dataFlow ? `<div class="emp-section-title">DATA FLOW</div>
    <div class="emp-dataflow">
      <div class="df-section"><span class="df-label">READS</span>${emp.dataFlow.reads.map(f => `<div class="df-file">${f.split('/').pop()}</div>`).join('')}</div>
      <div class="df-section"><span class="df-label">WRITES</span>${emp.dataFlow.writes.map(f => `<div class="df-file df-write">${f.split('/').pop()}</div>`).join('')}</div>
      <div class="df-section"><span class="df-label">FEEDS</span>${emp.dataFlow.feeds.map(f => `<div class="df-feed">${f}</div>`).join('')}</div>
    </div>` : ''}
    <div class="emp-section-title">RESPONSIBILITIES</div>
    ${emp.tasks.map(t => `<div class="emp-task">${t}</div>`).join('')}
    <div class="emp-section-title">RULES</div>
    ${emp.rules.map(r => `<div class="emp-rule">${r}</div>`).join('')}
  `;

  // Mini avatar
  setTimeout(() => {
    const ac = document.getElementById('avatar-canvas');
    if (!ac) return;
    const a = ac.getContext('2d');
    a.imageSmoothingEnabled = false;
    a.fillStyle = emp.hair;   a.fillRect(13,2,22,8);
    a.fillStyle = emp.skin;   a.fillRect(14,6,20,18);
    a.fillStyle = '#111';     a.fillRect(19,13,4,4); a.fillRect(27,13,4,4);
    a.fillStyle = '#fff';     a.fillRect(20,13,2,2); a.fillRect(28,13,2,2);
    a.fillStyle = emp.color;  a.fillRect(10,24,28,16);
    a.fillStyle = lightenColor(emp.color,1.2); a.fillRect(18,24,12,3);
    a.fillStyle = emp.pants;  a.fillRect(14,40,10,6); a.fillRect(24,40,10,6);
    a.fillStyle = emp.shoes;  a.fillRect(14,46,10,2); a.fillRect(24,46,10,2);
  }, 30);
}

function updateSidebar() {
  const dir = document.getElementById('directory-list');
  dir.innerHTML = ALL_CHARS.map(emp => {
    const status = getDeptStatus(emp.id);
    const apiIcons = (emp.apis||[]).map(a => `<span title="${a.name}" style="font-size:8px">${a.icon}</span>`).join('');
    return `<div class="dir-entry" data-id="${emp.id}">
      <div class="dir-avatar" style="background:${emp.color}"></div>
      <div class="dir-info">
        <div class="dir-name">${emp.name} <span style="color:${emp.color};font-size:6px">${emp.fullName}</span></div>
        <div class="dir-role">${emp.title}</div>
        <div class="dir-apis">${apiIcons}</div>
      </div>
      <div class="dir-status ${status}"></div>
    </div>`;
  }).join('');

  document.querySelectorAll('.dir-entry').forEach(el => {
    el.addEventListener('click', () => {
      const emp = ALL_CHARS.find(e => e.id === el.dataset.id);
      if (emp) selectEmployee(emp);
    });
  });

  document.getElementById('back-btn').onclick = () => {
    document.getElementById('directory-section').classList.remove('hidden');
    document.getElementById('employee-detail').classList.add('hidden');
    selectedEmployee = null;
  };

  renderQueue();
  renderEnforcerLog();
}

function renderQueue() {
  const list = document.getElementById('queue-list');
  if (!queueState || !(queueState.pending||[]).length) {
    list.innerHTML = '<div class="q-empty">No items pending</div>';
    return;
  }
  const DEPT_NAMES_Q = {intel:'Market Intel',seo:'SEO',content:'Content',email:'Email',social_morning:'Social',cro:'CRO',x_intel:'X Intel',dialer:'Dialer',image_prompts:'Image Prompts',blog_writer:'Blog Writer'};
  const skip = new Set(['id','department','type','summary']);
  list.innerHTML = queueState.pending.map(i => {
    const dept = i.department || '?';
    const deptName = DEPT_NAMES_Q[dept] || dept;
    const details = Object.entries(i).filter(([k])=>!skip.has(k)).slice(0,5).map(([k,v])=>{
      let val = typeof v === 'string' ? v : JSON.stringify(v);
      if(val.length>120) val = val.slice(0,120)+'…';
      return `<span class="q-detail-line"><b>${k}</b>: ${val}</span>`;
    }).join('');
    return `<div class="q-item" data-id="${i.id||''}">
      <span class="q-type">${(i.type||'ITEM').toUpperCase()}</span> <span class="q-dept">${deptName}</span>
      <div class="q-summary">${i.summary||i.description||i.title||'No description'}</div>
      ${details?`<div class="q-detail">${details}</div>`:''}
      <div class="q-actions">
        <button class="q-btn q-btn-approve" onclick="dashApprove('${i.id||''}')">APPROVE</button>
        <button class="q-btn q-btn-reject" onclick="dashReject('${i.id||''}')">REJECT</button>
      </div>
      <span class="q-id">${i.id||''}</span>
    </div>`;
  }).join('');
}

async function dashAction(itemId, action) {
  // Trigger via Telegram webhook worker (same API as /approve and /reject commands)
  const workerUrl = 'https://gadgetgeeks-telegram-webhook.gadgetgeeks.workers.dev';
  try {
    addNotification('info', `${action==='approve'?'Approving':'Rejecting'} ${itemId}...`);
    // We trigger the gm-queue workflow via GitHub API directly
    const resp = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/gm-queue.yml/dispatches`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${window._ghToken||''}`,
        'Accept': 'application/vnd.github.v3+json',
      },
      body: JSON.stringify({ ref: 'main', inputs: { boss_department: 'gm_queue', boss_instruction: `${action} ${itemId}` } }),
    });
    if (resp.status === 204) {
      addNotification('info', `${action==='approve'?'Approved':'Rejected'}: ${itemId}`);
      addEnforcerLog('ok', `BOSS ${action}d item ${itemId.slice(-8)}`);
      // Optimistically remove from queue display
      const el = document.querySelector(`.q-item[data-id="${itemId}"]`);
      if (el) { el.style.opacity = '0.3'; el.querySelectorAll('.q-btn').forEach(b => b.disabled = true); }
    } else {
      addNotification('alert', `Failed to ${action} — check token`);
    }
  } catch (e) {
    addNotification('alert', `Error: ${e.message}`);
  }
}
function dashApprove(id) { dashAction(id, 'approve'); }
function dashReject(id) { dashAction(id, 'reject'); }

function renderEnforcerLog() {
  const el = document.getElementById('enforcer-log');
  if (!enforcerLog.length) {
    el.innerHTML = '<div class="enforcer-entry info"><span class="enforcer-time">--:--</span> BOSS monitoring all departments</div>';
    return;
  }
  el.innerHTML = enforcerLog.slice(-12).reverse().map(e =>
    `<div class="enforcer-entry ${e.type}"><span class="enforcer-time">${e.time}</span> ${e.msg}</div>`
  ).join('');
}

// ═══════════════════════════════════════════
// HUD & SCHEDULE
// ═══════════════════════════════════════════
function updateHUD() {
  const now = new Date();
  document.getElementById('hud-time').textContent = pad(now.getUTCHours())+':'+pad(now.getUTCMinutes())+' UTC';
  document.getElementById('hud-date').textContent = now.toUTCString().slice(0,16);
  if (!masterState) return;
  let working=0, idle=0;
  for (const e of [...EMPLOYEES, X_INTEL, IMAGE_PROMPT, PROMPT_QA, BLOG_WRITER, BLOG_QA, BLOG_PUBLISHER]) { const s=getDeptStatus(e.id); if(s==='working')working++; else if(s==='idle')idle++; }
  document.getElementById('hud-working').textContent = working;
  document.getElementById('hud-idle').textContent = idle;
  document.getElementById('hud-queue').textContent = queueState?(queueState.pending||[]).length:0;
}

function updateScheduleBar() {
  const tl = document.getElementById('schedule-timeline');
  const now = new Date();
  const day = now.getUTCDay();
  const mins = now.getUTCHours()*60 + now.getUTCMinutes();
  const sched = [
    {t:'05:17',m:317,l:'SEO Deep',d:[1],c:'#0f8'},{t:'06:23',m:383,l:'SEO',d:[0,1,2,3,4,5,6],c:'#0f8'},
    {t:'07:00',m:420,l:'X-Intel',d:[0,1,2,3,4,5,6],c:'#1DA1F2'},
    {t:'07:03',m:423,l:'GM Report',d:[5],c:'#a6f'},{t:'07:41',m:461,l:'Content',d:[1,3,5],c:'#f84'},{t:'08:19',m:499,l:'LENS',d:[1,3,5],c:'#e879f9'},{t:'08:49',m:529,l:'FOCUS',d:[1,3,5],c:'#f59e0b'},
    {t:'08:53',m:533,l:'Email',d:[2,4],c:'#fc0'},{t:'09:11',m:551,l:'Social AM',d:[0,1,2,3,4,5,6],c:'#f6a'},
    {t:'09:30',m:570,l:'SCRIBE',d:[1,3,5],c:'#10b981'},{t:'10:00',m:600,l:'QUILL',d:[1,3,5],c:'#ef4444'},{t:'10:30',m:630,l:'PRESS',d:[1,3,5],c:'#6366f1'},
    {t:'10:47',m:647,l:'Intel',d:[1,4],c:'#0cf'},{t:'11:29',m:689,l:'CRO',d:[3],c:'#48f'},
    {t:'14:15',m:855,l:'DIALER',d:[1,2,3,4,5],c:'#16a34a'},{t:'15:45',m:945,l:'CALLS',d:[1,2,3,4,5],c:'#16a34a'},
    {t:'16:37',m:997,l:'Social PM',d:[0,1,2,3,4,5,6],c:'#f6a'},{t:'18:51',m:1131,l:'GM Queue',d:[0,1,2,3,4,5,6],c:'#a6f'},
  ].filter(s=>s.d.includes(day));
  tl.innerHTML = sched.map(s => {
    const cls = mins>=s.m&&mins<s.m+30?'active':mins<s.m?'next':'done';
    return `<div class="sched-block ${cls}" style="border-color:${s.c}"><span class="sched-time">${s.t}</span> ${s.l}</div>`;
  }).join('') || '<div class="sched-block" style="color:#667">No runs today</div>';
}

// ═══════════════════════════════════════════
// DATA
// ═══════════════════════════════════════════
async function fetchJSON(path) {
  for (const u of [`../${path}`,`${RAW}/${path}`]) {
    try { const r=await fetch(u,{cache:'no-store'}); if(r.ok) return await r.json(); } catch(e){}
  }
  return null;
}

async function loadData() {
  const [m,q] = await Promise.all([fetchJSON('state/master.json'),fetchJSON('state/queue.json')]);
  masterState=m; queueState=q;
  updateSidebar(); updateHUD(); updateScheduleBar();
  runEnforcer(); loadImagePrompts(); loadBlogPipeline();
}

function runEnforcer() {
  if(!masterState) return;
  const pending = queueState?(queueState.pending||[]).length:0;
  if (pending > 3) {
    addEnforcerLog('warn',`${pending} items in queue — needs review`);
    addNotification('warn',`${pending} items need your approval`);
  }
  for (const emp of EMPLOYEES) {
    const s = getDeptStatus(emp.id);
    if (s==='error') addEnforcerLog('alert',`${emp.name} in ERROR state`);
  }
}

// ═══════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════
function getDeptStatus(id) {
  if(!masterState) return 'idle';
  const d=masterState.departments||{};
  const emp=ALL_CHARS.find(e=>e.id===id); if(!emp) return 'idle';
  let st='idle';
  for(const k of emp.stateKeys){const s=d[k]; if(s){if(s.status==='running')return'working';if(s.status==='error')st='error';if(s.status==='ok'&&st==='idle')st='ok';}}
  return st;
}
function getLastRun(id) {
  if(!masterState) return null;
  const d=masterState.departments||{};
  const emp=ALL_CHARS.find(e=>e.id===id); if(!emp) return null;
  let lr=null;
  for(const k of emp.stateKeys){const s=d[k]; if(s&&s.last_run){if(!lr||new Date(s.last_run)>new Date(lr))lr=s.last_run;}}
  return lr;
}
function getTotalRuns(id) {
  if(!masterState) return 0;
  const d=masterState.departments||{};
  const emp=ALL_CHARS.find(e=>e.id===id); if(!emp) return 0;
  let t=0; for(const k of emp.stateKeys){const s=d[k]; if(s)t+=s.runs_total||0;} return t;
}
function getNextRun(emp) {
  const now=new Date();
  for(let d=0;d<8;d++){const c=new Date(now);c.setUTCDate(c.getUTCDate()+d);c.setUTCHours(emp.cronH,emp.cronM,0,0);
    if(c>now&&emp.cronDays.includes(c.getUTCDay())){const diff=c-now;const h=Math.floor(diff/36e5);const m=Math.floor((diff%36e5)/6e4);return h>24?`${Math.floor(h/24)}d ${h%24}h`:`${h}h ${m}m`;}}
  return null;
}
function timeAgo(s){if(!s)return'Never';const d=Date.now()-new Date(s);const m=Math.floor(d/6e4);const h=Math.floor(d/36e5);if(m<1)return'Just now';if(m<60)return m+'m ago';if(h<24)return h+'h ago';return Math.floor(d/864e5)+'d ago';}
function pad(n){return String(n).padStart(2,'0');}
function lightenColor(hex,f){const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);return`rgb(${Math.min(255,Math.floor(r*f))},${Math.min(255,Math.floor(g*f))},${Math.min(255,Math.floor(b*f))})`;}
function darkenColor(hex,f){return lightenColor(hex,f);}
function pickRandom(arr){return arr[Math.floor(Math.random()*arr.length)];}
function addEnforcerLog(type,msg){const t=pad(new Date().getUTCHours())+':'+pad(new Date().getUTCMinutes());enforcerLog.push({type,msg,time:t});if(enforcerLog.length>50)enforcerLog.shift();renderEnforcerLog();}
function addNotification(type,msg){const el=document.getElementById('notifications');const n=document.createElement('div');n.className=`notif ${type}`;n.textContent=msg;el.appendChild(n);setTimeout(()=>n.remove(),4000);}

// ═══════════════════════════════════════════
// BLOG PIPELINE
// ═══════════════════════════════════════════
let blogPipelineData = null;

async function loadBlogPipeline() {
  blogPipelineData = await fetchJSON('departments/content/blog-pipeline.json');
  renderBlogPipeline();
}

function renderBlogPipeline() {
  const statsEl = document.getElementById('blog-pipeline-stats');
  const listEl = document.getElementById('blog-pipeline-list');
  if (!blogPipelineData) {
    statsEl.innerHTML = '';
    listEl.innerHTML = '<div class="bp-empty">No blogs in pipeline yet — SCRIBE hasn\'t run</div>';
    return;
  }

  const ps = blogPipelineData.pipeline_stats || {};
  statsEl.innerHTML = `
    <div class="bp-stat"><span class="bp-stat-val" style="color:var(--yellow)">${ps.total_drafted||0}</span><span class="bp-stat-label">DRAFTED</span></div>
    <div class="bp-stat"><span class="bp-stat-val" style="color:var(--green)">${ps.total_approved||0}</span><span class="bp-stat-label">APPROVED</span></div>
    <div class="bp-stat"><span class="bp-stat-val" style="color:var(--red)">${ps.total_rejected||0}</span><span class="bp-stat-label">REJECTED</span></div>
    <div class="bp-stat"><span class="bp-stat-val" style="color:var(--cyan)">${ps.total_published||0}</span><span class="bp-stat-label">PUBLISHED</span></div>
  `;

  const blogs = blogPipelineData.blogs || [];
  if (!blogs.length) {
    listEl.innerHTML = '<div class="bp-empty">Pipeline empty — SCRIBE will draft blogs Mon/Wed/Fri</div>';
    return;
  }

  listEl.innerHTML = blogs.slice(-10).reverse().map(b => {
    const status = (b.status||'unknown').replace(/_/g,' ');
    const statusClass = status.includes('approved') ? 'approved' : status.includes('reject') ? 'rejected' : status.includes('publish') ? 'published' : status.includes('queued') ? 'queued' : status.includes('block') ? 'blocked' : 'draft';
    const keywords = (b.target_keywords||[]).slice(0,3);
    return `<div class="bp-blog">
      <div class="bp-blog-title">${b.title||'Untitled'}</div>
      <div class="bp-blog-meta">
        <span class="bp-status ${statusClass}">${status.toUpperCase()}</span>
        ${b.qa_score?`<span class="bp-keyword">QA: ${b.qa_score}</span>`:''}
        ${keywords.map(k => `<span class="bp-keyword">${k}</span>`).join('')}
      </div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════
// IMAGE GALLERY
// ═══════════════════════════════════════════
let imagePromptsData = null;

async function loadImagePrompts() {
  imagePromptsData = await fetchJSON('departments/social/image-prompts.json');
  renderGallery();
}

function renderGallery() {
  const statsEl = document.getElementById('gallery-stats');
  const foldersEl = document.getElementById('gallery-folders');
  if (!imagePromptsData) {
    statsEl.innerHTML = '';
    foldersEl.innerHTML = '<div class="gal-empty">No image prompts yet — LENS hasn\'t run</div>';
    return;
  }

  // Stats bar
  const qa = imagePromptsData.qa_summary || {};
  const total = (imagePromptsData.prompts||[]).length;
  const folderTotal = Object.values(imagePromptsData.folders||{}).reduce((s,f) => s + (f.prompts||[]).length, 0);
  const allTotal = total + folderTotal;
  statsEl.innerHTML = `
    <div class="gal-stat"><span class="gal-stat-val" style="color:var(--white)">${allTotal}</span><span class="gal-stat-label">TOTAL</span></div>
    <div class="gal-stat"><span class="gal-stat-val" style="color:var(--green)">${qa.excellent||0}</span><span class="gal-stat-label">EXCELLENT</span></div>
    <div class="gal-stat"><span class="gal-stat-val" style="color:var(--cyan)">${qa.good||0}</span><span class="gal-stat-label">GOOD</span></div>
    <div class="gal-stat"><span class="gal-stat-val" style="color:var(--yellow)">${qa.needs_work||0}</span><span class="gal-stat-label">NEEDS WORK</span></div>
    <div class="gal-stat"><span class="gal-stat-val" style="color:var(--red)">${qa.blocked||0}</span><span class="gal-stat-label">BLOCKED</span></div>
  `;

  // Folders
  const folders = imagePromptsData.folders || {};
  if (!Object.keys(folders).length && !allTotal) {
    foldersEl.innerHTML = '<div class="gal-empty">LENS hasn\'t generated prompts yet.<br>Next run will populate folders.</div>';
    return;
  }

  // Unfoldered prompts as a pseudo-folder
  let html = '';
  if (total > 0) {
    html += `<div class="gal-folder" data-folder="__root"><span class="gal-folder-count">${total}</span><div class="gal-folder-name">Uncategorized</div><div class="gal-folder-desc">Prompts not yet sorted into folders</div></div>`;
  }
  for (const [key, folder] of Object.entries(folders)) {
    const count = (folder.prompts||[]).length;
    html += `<div class="gal-folder" data-folder="${key}"><span class="gal-folder-count">${count}</span><div class="gal-folder-name">${folder.label||key}</div><div class="gal-folder-desc">${folder.description||''}</div></div>`;
  }
  foldersEl.innerHTML = html;

  // Click handlers
  foldersEl.querySelectorAll('.gal-folder').forEach(el => {
    el.addEventListener('click', () => openGalleryFolder(el.dataset.folder));
  });

  document.getElementById('gallery-back-btn').onclick = () => {
    document.getElementById('gallery-detail').classList.add('hidden');
    foldersEl.classList.remove('hidden');
    statsEl.classList.remove('hidden');
  };
}

function openGalleryFolder(folderKey) {
  const foldersEl = document.getElementById('gallery-folders');
  const statsEl = document.getElementById('gallery-stats');
  const detailEl = document.getElementById('gallery-detail');
  const promptsEl = document.getElementById('gallery-prompts');

  foldersEl.classList.add('hidden');
  statsEl.classList.add('hidden');
  detailEl.classList.remove('hidden');

  let prompts;
  if (folderKey === '__root') {
    prompts = imagePromptsData.prompts || [];
  } else {
    prompts = (imagePromptsData.folders && imagePromptsData.folders[folderKey]) ? imagePromptsData.folders[folderKey].prompts || [] : [];
  }

  if (!prompts.length) {
    promptsEl.innerHTML = '<div class="gal-empty">No prompts in this folder yet</div>';
    return;
  }

  promptsEl.innerHTML = prompts.map((p, idx) => {
    const rating = (p.rating||p.verdict||p.qa_status||'unreviewed').toLowerCase().replace(/[_ ]/g,'');
    const scoreClass = rating.includes('excellent') ? 'excellent' : rating.includes('good') ? 'good' : rating.includes('need')||rating.includes('fix') ? 'needswork' : rating.includes('block') ? 'blocked' : 'good';
    const score = p.score != null ? `${p.score}/15` : '--';
    const promptText = p.prompt || p.corrected_prompt || p.text || JSON.stringify(p).slice(0,300);
    const platform = p.platform || p.target_platform || '';
    const aspect = p.aspect_ratio || '';
    const useCase = p.use_case || folderKey;
    const negPrompt = p.negative_prompt || '';
    const params = p.platform_params || '';
    const tool = p.recommended_tool || '';
    const notes = p.notes || '';
    const pid = p.id || p.prompt_id || `prompt_${idx}`;
    const imgUrl = p.generated_url || '';
    const genStatus = p.generation_status || '';
    const genError = p.generation_error || '';
    return `<div class="gal-prompt" data-prompt-id="${pid}">
      <div class="gal-prompt-header">
        <span class="gal-prompt-id">${pid}</span>
        <span class="gal-prompt-score gal-score-${scoreClass}">${score} ${(p.rating||p.verdict||p.qa_status||'UNREVIEWED').toUpperCase()}</span>
      </div>
      ${imgUrl?`<div class="gal-image-wrap"><img class="gal-image" src="${imgUrl}" alt="${pid}" loading="lazy" onclick="window.open('${imgUrl}','_blank')"/><span class="gal-image-badge">GENERATED</span></div>`
        :genStatus==='error'?`<div class="gal-image-placeholder error">GENERATION FAILED<br><span style="font-size:5px">${genError.slice(0,100)}</span></div>`
        :`<div class="gal-image-placeholder">NOT YET GENERATED<br><span style="font-size:5px">Run /run image_generate or wait for next scheduled run</span></div>`}
      <div class="gal-prompt-text">${promptText.length>600?promptText.slice(0,600)+'...':promptText}</div>
      ${negPrompt?`<div class="gal-neg-prompt"><b>Negative:</b> ${negPrompt.slice(0,200)}</div>`:''}
      ${notes?`<div class="gal-notes"><b>Notes:</b> ${notes.slice(0,150)}</div>`:''}
      <div class="gal-prompt-meta">
        ${tool?`<span class="gal-meta-tag tool">${tool}</span>`:''}
        ${platform?`<span class="gal-meta-tag">${platform}</span>`:''}
        ${aspect?`<span class="gal-meta-tag">${aspect}</span>`:''}
        ${useCase?`<span class="gal-meta-tag">${useCase}</span>`:''}
        ${params?`<span class="gal-meta-tag">${params}</span>`:''}
      </div>
      <div class="gal-actions">
        <button class="q-btn q-btn-approve" onclick="copyPrompt(this)">COPY PROMPT</button>
        <button class="q-btn q-btn-expand" onclick="sendPromptFeedback('${pid}','approve')">APPROVE</button>
        <button class="q-btn q-btn-reject" onclick="sendPromptFeedback('${pid}','reject')">REJECT</button>
      </div>
    </div>`;
  }).join('');

  // Store raw prompts for copy
  promptsEl._prompts = prompts;
}

// ═══════════════════════════════════════════
// IMAGE PROMPT ACTIONS
// ═══════════════════════════════════════════
function copyPrompt(btn) {
  const card = btn.closest('.gal-prompt');
  const promptText = card.querySelector('.gal-prompt-text').textContent;
  navigator.clipboard.writeText(promptText).then(() => {
    btn.textContent = 'COPIED!';
    addNotification('info', 'Prompt copied to clipboard');
    setTimeout(() => { btn.textContent = 'COPY PROMPT'; }, 2000);
  }).catch(() => {
    // Fallback for no clipboard API
    const ta = document.createElement('textarea');
    ta.value = promptText;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    btn.textContent = 'COPIED!';
    setTimeout(() => { btn.textContent = 'COPY PROMPT'; }, 2000);
  });
}

async function sendPromptFeedback(promptId, action) {
  addNotification('info', `${action === 'approve' ? 'Approving' : 'Rejecting'} prompt ${promptId}...`);
  try {
    await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/gm-queue.yml/dispatches`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${window._ghToken||''}`, 'Accept': 'application/vnd.github.v3+json' },
      body: JSON.stringify({ ref: 'main', inputs: { boss_department: 'image_prompts', boss_instruction: `${action} prompt ${promptId}` } }),
    });
    addNotification('info', `Prompt ${promptId} ${action}d`);
    addEnforcerLog('ok', `BOSS ${action}d prompt ${promptId.slice(-8)}`);
    const el = document.querySelector(`.gal-prompt[data-prompt-id="${promptId}"]`);
    if (el) el.style.opacity = '0.4';
  } catch (e) {
    addNotification('alert', `Failed: ${e.message}`);
  }
}

// ═══════════════════════════════════════════
// COMMS CENTER
// ═══════════════════════════════════════════
let commsMessages = [];
let commsTarget = 'gm';

function initComms() {
  const DEPT_NAMES_C = {gm:'GM',intel:'Intel',seo:'SEO',content:'Content',email:'Email',social_morning:'Social',cro:'CRO',x_intel:'X Intel',dialer:'Xavier',image_prompts:'Lens',blog_writer:'Scribe'};

  // Build tabs from dropdown options
  const tabs = document.getElementById('comms-tabs');
  const deptSelect = document.getElementById('comms-dept');
  tabs.innerHTML = '';
  for (const opt of deptSelect.options) {
    const btn = document.createElement('button');
    btn.className = 'comms-tab' + (opt.value === commsTarget ? ' active' : '');
    btn.dataset.target = opt.value;
    btn.textContent = DEPT_NAMES_C[opt.value] || opt.value;
    btn.addEventListener('click', () => {
      commsTarget = opt.value;
      deptSelect.value = opt.value;
      tabs.querySelectorAll('.comms-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      renderComms();
    });
    tabs.appendChild(btn);
  }

  // Sync select with tabs
  deptSelect.addEventListener('change', () => {
    commsTarget = deptSelect.value;
    tabs.querySelectorAll('.comms-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.target === commsTarget);
    });
    renderComms();
  });

  // Send button
  document.getElementById('comms-send').addEventListener('click', sendCommsMessage);
  document.getElementById('comms-msg').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendCommsMessage();
  });

  // Load existing boss instructions from run history
  loadCommsHistory();
}

async function loadCommsHistory() {
  const history = await fetchJSON('state/run-history.json');
  if (!history) return;

  const runs = history.runs || [];
  commsMessages = [];

  for (const run of runs.slice(-20)) {
    const dept = run.department || '?';
    const ts = run.timestamp || '';
    const summary = run.summary || '';
    if (summary) {
      commsMessages.push({ from: dept, type: 'dept', text: summary.slice(0, 200), time: ts });
    }
    if (run.had_boss_instructions) {
      commsMessages.push({ from: 'boss', type: 'boss', text: `Instruction sent to ${dept}`, time: ts });
    }
  }

  // Also load queue items as dept messages
  if (queueState && queueState.pending) {
    for (const item of queueState.pending) {
      commsMessages.push({
        from: item.department || '?',
        type: 'dept',
        text: `[Needs Approval] ${item.summary || item.type || 'New item'}`,
        time: new Date().toISOString(),
        dept: item.department,
      });
    }
  }

  renderComms();
}

function renderComms() {
  const feed = document.getElementById('comms-feed');
  const filtered = commsTarget === 'gm'
    ? commsMessages
    : commsMessages.filter(m => m.from === commsTarget || m.dept === commsTarget || m.from === 'boss');

  if (!filtered.length) {
    feed.innerHTML = '<div class="comms-empty">No messages yet — send an instruction below</div>';
    return;
  }

  const DEPT_NAMES_C = {gm:'GM',intel:'Intel',seo:'SEO',content:'Content',email:'Email',social_morning:'Social',cro:'CRO',x_intel:'X Intel',dialer:'Xavier',image_prompts:'Lens',blog_writer:'Scribe',boss:'BOSS'};

  feed.innerHTML = filtered.slice(-15).map(m => {
    let timeStr = '';
    if (m.time) {
      try { const d = new Date(m.time); timeStr = pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()); } catch(e) {}
    }
    return `<div class="comms-msg ${m.type}">
      <span class="comms-from">${DEPT_NAMES_C[m.from]||m.from}<span class="comms-time">${timeStr}</span></span>
      <span class="comms-text">${m.text}</span>
    </div>`;
  }).join('');

  feed.scrollTop = feed.scrollHeight;
}

async function sendCommsMessage() {
  const input = document.getElementById('comms-msg');
  const dept = document.getElementById('comms-dept').value;
  const text = input.value.trim();
  if (!text) return;

  input.value = '';

  // Add to local feed immediately
  commsMessages.push({ from: 'boss', type: 'boss', text: `[→ ${dept}] ${text}`, time: new Date().toISOString() });
  renderComms();

  // Trigger via GitHub workflow dispatch (same as /boss command)
  const DEPT_WF = {intel:'intel.yml',seo:'seo-daily.yml',content:'content.yml',email:'email.yml',social_morning:'social-morning.yml',cro:'cro.yml',x_intel:'x-intel.yml',dialer:'dialer.yml',image_prompts:'image-prompts.yml',blog_writer:'blog-writer.yml',gm:'gm-queue.yml'};
  const workflow = DEPT_WF[dept] || 'gm-queue.yml';

  try {
    // Save boss instruction via gm-queue dispatch
    await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/gm-queue.yml/dispatches`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${window._ghToken||''}`, 'Accept': 'application/vnd.github.v3+json' },
      body: JSON.stringify({ ref: 'main', inputs: { boss_department: dept, boss_instruction: text.slice(0, 500) } }),
    });

    // Also trigger the department workflow
    if (dept !== 'gm') {
      await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${workflow}/dispatches`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${window._ghToken||''}`, 'Accept': 'application/vnd.github.v3+json' },
        body: JSON.stringify({ ref: 'main' }),
      });
    }

    addNotification('info', `Instruction sent to ${dept}`);
    addEnforcerLog('ok', `BOSS sent instruction to ${dept}`);
  } catch (e) {
    addNotification('alert', `Send failed: ${e.message}`);
  }
}

// ═══════════════════════════════════════════
// TOUCH HANDLERS (mobile support)
// ═══════════════════════════════════════════
function onTouchTap(e) {
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width / rect.width, sy = canvas.height / rect.height;
  const mx = (touch.clientX - rect.left) * sx;
  const my = (touch.clientY - rect.top) * sy;

  // Find tapped employee
  for (const emp of ALL_CHARS) {
    const c = chars[emp.id];
    const ex = c.x - T/2, ey = c.y - T/2;
    if (mx >= ex-8 && mx <= ex+T+8 && my >= ey-18 && my <= ey+T+12) {
      selectEmployee(emp);
      return;
    }
  }
  // Hide tooltip on tap-away
  document.getElementById('tooltip').classList.add('hidden');
}

function onTouchMove(e) {
  // Prevent canvas from scrolling page when dragging on it
  if (e.target === canvas) e.preventDefault();
}

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════
async function init() {
  canvas = document.getElementById('office');
  ctx = canvas.getContext('2d');
  canvas.width = W;
  canvas.height = H;

  initChars();

  canvas.addEventListener('mousemove', onMouseMove);
  canvas.addEventListener('click', onClick);

  // Touch support for mobile
  canvas.addEventListener('touchstart', onTouchTap, {passive: false});
  canvas.addEventListener('touchmove', onTouchMove, {passive: false});

  // GH token for approve/reject/comms (stored in sessionStorage)
  window._ghToken = sessionStorage.getItem('ghToken') || '';
  if (!window._ghToken) {
    const t = prompt('Enter GitHub token for dashboard actions (approve/reject/send):\n(Leave blank for read-only mode)');
    if (t) { window._ghToken = t; sessionStorage.setItem('ghToken', t); }
  }

  await loadData();
  setInterval(loadData, 30000);
  setInterval(()=>{updateHUD();},1000);

  initComms();

  addEnforcerLog('info','BOSS online — monitoring all departments');
  addEnforcerLog('info','God Mode activated');

  requestAnimationFrame(gameLoop);
}

init();
