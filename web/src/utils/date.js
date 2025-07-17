/**
 * Format a date string or timestamp into a human-readable format
 * @param {string|number|Date} date - The date to format
 * @param {string} [format='YYYY-MM-DD HH:mm:ss'] - Optional format string
 * @returns {string} Formatted date string
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '';
  
  const d = new Date(date);
  
  if (isNaN(d.getTime())) {
    return '';
  }

  const pad = (num) => String(num).padStart(2, '0');
  
  const formats = {
    YYYY: d.getFullYear(),
    MM: pad(d.getMonth() + 1),
    DD: pad(d.getDate()),
    HH: pad(d.getHours()),
    mm: pad(d.getMinutes()),
    ss: pad(d.getSeconds())
  };

  return format.replace(/YYYY|MM|DD|HH|mm|ss/g, match => formats[match]);
} 