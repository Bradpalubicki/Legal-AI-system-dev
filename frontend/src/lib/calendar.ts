/**
 * Calendar Export Utilities
 * Generates iCal format files for calendar applications
 */

import { TimelineEvent } from './api/cases';

/**
 * Format date for iCal format (YYYYMMDDTHHMMSSZ)
 */
function formatICalDate(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');

  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

/**
 * Escape special characters in iCal text fields
 */
function escapeICalText(text: string): string {
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n');
}

/**
 * Generate a unique ID for an event
 */
function generateEventId(event: TimelineEvent): string {
  return `${event.id}@legal-ai-system`;
}

/**
 * Convert a single timeline event to iCal VEVENT format
 */
function eventToICalEvent(event: TimelineEvent, caseName: string): string {
  const startDate = new Date(event.event_date);
  const endDate = new Date(startDate.getTime() + (60 * 60 * 1000)); // 1 hour duration
  const now = new Date();

  const title = escapeICalText(event.title);
  const description = event.description
    ? escapeICalText(`${event.description}\n\nCase: ${caseName}\nType: ${event.event_type}\nStatus: ${event.status}`)
    : escapeICalText(`Case: ${caseName}\nType: ${event.event_type}\nStatus: ${event.status}`);
  const location = event.location ? escapeICalText(event.location) : '';

  let icalEvent = 'BEGIN:VEVENT\r\n';
  icalEvent += `UID:${generateEventId(event)}\r\n`;
  icalEvent += `DTSTAMP:${formatICalDate(now)}\r\n`;
  icalEvent += `DTSTART:${formatICalDate(startDate)}\r\n`;
  icalEvent += `DTEND:${formatICalDate(endDate)}\r\n`;
  icalEvent += `SUMMARY:${title}\r\n`;

  if (description) {
    icalEvent += `DESCRIPTION:${description}\r\n`;
  }

  if (location) {
    icalEvent += `LOCATION:${location}\r\n`;
  }

  // Add status
  if (event.status === 'completed') {
    icalEvent += `STATUS:CONFIRMED\r\n`;
  } else if (event.status === 'cancelled') {
    icalEvent += `STATUS:CANCELLED\r\n`;
  } else {
    icalEvent += `STATUS:TENTATIVE\r\n`;
  }

  // Add categories based on event type
  icalEvent += `CATEGORIES:Legal,${event.event_type}\r\n`;

  icalEvent += 'END:VEVENT\r\n';

  return icalEvent;
}

/**
 * Export timeline events to iCal format
 */
export function exportTimelineToICal(
  events: TimelineEvent[],
  caseName: string = 'Legal Case'
): void {
  if (events.length === 0) {
    alert('No events to export');
    return;
  }

  // Filter out only scheduled events
  const scheduledEvents = events.filter(e => e.status === 'scheduled' || e.status === 'completed');

  if (scheduledEvents.length === 0) {
    alert('No scheduled events to export');
    return;
  }

  // Build iCal content
  let icalContent = 'BEGIN:VCALENDAR\r\n';
  icalContent += 'VERSION:2.0\r\n';
  icalContent += 'PRODID:-//Legal AI System//Case Management//EN\r\n';
  icalContent += 'CALSCALE:GREGORIAN\r\n';
  icalContent += 'METHOD:PUBLISH\r\n';
  icalContent += `X-WR-CALNAME:${escapeICalText(caseName)}\r\n`;
  icalContent += `X-WR-CALDESC:Legal case events for ${escapeICalText(caseName)}\r\n`;
  icalContent += 'X-WR-TIMEZONE:UTC\r\n';

  // Add all events
  for (const event of scheduledEvents) {
    icalContent += eventToICalEvent(event, caseName);
  }

  icalContent += 'END:VCALENDAR\r\n';

  // Create and download file
  const blob = new Blob([icalContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;

  // Generate filename
  const safeFileName = caseName
    .replace(/[^a-z0-9]/gi, '_')
    .toLowerCase()
    .substring(0, 50);
  const dateStr = new Date().toISOString().split('T')[0];
  link.download = `${safeFileName}_events_${dateStr}.ics`;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export a single event to iCal format
 */
export function exportSingleEventToICal(
  event: TimelineEvent,
  caseName: string = 'Legal Case'
): void {
  exportTimelineToICal([event], caseName);
}
