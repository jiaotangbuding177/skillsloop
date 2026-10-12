// Synthetic initial project utility; not a completed task solution.
const fs = require('fs');
function loadRecords(path) { const rows=JSON.parse(fs.readFileSync(path,'utf8')); if (!Array.isArray(rows)) throw new Error('records must be an array'); return rows; }
module.exports = {loadRecords};
