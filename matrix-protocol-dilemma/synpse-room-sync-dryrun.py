#!/usr/bin/env python3
"""
Dry-run version of the Matrix Synapse Room Sync Script
Shows what would be copied without actually modifying the target database
"""

import sqlite3
import sys
from typing import Optional


def dry_run_sync(input_db_path: str, target_db_path: str, room_id: str):
    """Preview what would be synced without making changes"""
    
    print(f"\n{'='*60}")
    print(f"DRY RUN - Preview sync for room: {room_id}")
    print(f"{'='*60}\n")
    
    # Connect to databases (read-only for target)
    print(f"Connecting to input DB: {input_db_path}")
    input_conn = sqlite3.connect(input_db_path)
    input_conn.row_factory = sqlite3.Row
    
    print(f"Connecting to target DB: {target_db_path} (read-only)")
    target_conn = sqlite3.connect(f"file:{target_db_path}?mode=ro", uri=True)
    target_conn.row_factory = sqlite3.Row
    
    # Get current max stream_ordering
    target_cursor = target_conn.cursor()
    target_cursor.execute("SELECT MAX(stream_ordering) as max_order FROM events")
    result = target_cursor.fetchone()
    max_stream_ordering = result['max_order'] if result['max_order'] is not None else 0
    print(f"Current max stream_ordering in target DB: {max_stream_ordering}\n")
    
    # Get existing topological orderings in target
    target_cursor.execute(
        "SELECT topological_ordering, event_id FROM events WHERE room_id = ?",
        (room_id,)
    )
    existing_topological = {row['topological_ordering']: row['event_id'] for row in target_cursor.fetchall()}
    print(f"Found {len(existing_topological)} existing events in target DB for room\n")
    
    # Get all events from input DB
    input_cursor = input_conn.cursor()
    input_cursor.execute(
        """
        SELECT event_id, topological_ordering, stream_ordering, type, sender
        FROM events 
        WHERE room_id = ? 
        ORDER BY topological_ordering ASC
        """,
        (room_id,)
    )
    input_events = input_cursor.fetchall()
    print(f"Found {len(input_events)} events in input DB for room\n")
    
    if not input_events:
        print("No events to sync!")
        return
    
    # Simulate sync
    print(f"{'='*60}")
    print("Preview of changes:")
    print(f"{'='*60}\n")
    
    events_to_copy = []
    events_to_skip = []
    new_stream_ordering = max_stream_ordering
    
    for event in input_events:
        topological_ordering = event['topological_ordering']
        event_id = event['event_id']
        
        if topological_ordering in existing_topological:
            events_to_skip.append(event)
        else:
            new_stream_ordering += 1
            events_to_copy.append({
                'event': event,
                'new_stream_ordering': new_stream_ordering,
                'old_stream_ordering': event['stream_ordering']
            })
    
    # Show summary
    print(f"📊 Summary:")
    print(f"  Total events in input:     {len(input_events)}")
    print(f"  Events already in target:  {len(events_to_skip)}")
    print(f"  Events to be copied:       {len(events_to_copy)}")
    
    if events_to_copy:
        print(f"\n  New stream_ordering range: {max_stream_ordering + 1} to {new_stream_ordering}")
        print(f"  Stream ordering increment: +{len(events_to_copy)}")
    
    # Show events to copy
    if events_to_copy:
        print(f"\n{'='*60}")
        print(f"Events to be copied ({len(events_to_copy)} total):")
        print(f"{'='*60}\n")
        
        # Show first 20 and last 5
        show_events = events_to_copy[:20] if len(events_to_copy) <= 25 else events_to_copy[:20] + events_to_copy[-5:]
        
        for i, item in enumerate(show_events):
            event = item['event']
            new_so = item['new_stream_ordering']
            old_so = item['old_stream_ordering']
            
            if i == 20 and len(events_to_copy) > 25:
                print(f"\n  ... {len(events_to_copy) - 25} more events ...\n")
            
            print(f"  {i+1}. Event: {event['event_id'][:40]}...")
            print(f"     Type: {event['type']}")
            print(f"     Sender: {event['sender']}")
            print(f"     Topological: {event['topological_ordering']}")
            print(f"     Stream ordering: {old_so} → {new_so} ({"+" if new_so > old_so else ""}{new_so - old_so})")
            print()
    
    # Show events to skip (first 10 only)
    if events_to_skip:
        print(f"{'='*60}")
        print(f"Events to be skipped (already exist - showing first 10 of {len(events_to_skip)}):")
        print(f"{'='*60}\n")
        
        for i, event in enumerate(events_to_skip[:10]):
            print(f"  {i+1}. {event['event_id'][:40]}... (topological={event['topological_ordering']})")
    
    # Check event_json
    print(f"\n{'='*60}")
    print("Checking related tables...")
    print(f"{'='*60}\n")
    
    tables_to_check = [
        "event_json",
        "event_edges", 
        "event_auth",
        "state_events",
        "event_search",
        "event_to_state_groups"
    ]
    
    for table_name in tables_to_check:
        # Check if table exists in input DB
        input_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not input_cursor.fetchone():
            print(f"  {table_name}: ⚠ Table does not exist in input DB")
            continue
        
        events_with_data = 0
        events_without_data = 0
        
        # Check a sample of events (first 50)
        for item in events_to_copy[:50]:
            event_id = item['event']['event_id']
            input_cursor.execute(f"SELECT 1 FROM {table_name} WHERE event_id = ?", (event_id,))
            if input_cursor.fetchone():
                events_with_data += 1
            else:
                events_without_data += 1
        
        total_checked = min(50, len(events_to_copy))
        
        if events_with_data > 0:
            percentage = (events_with_data / total_checked) * 100
            print(f"  {table_name}: {events_with_data}/{total_checked} events have entries ({percentage:.1f}%)")
        else:
            print(f"  {table_name}: No entries found in sampled events")
    
    # Final summary
    print(f"\n{'='*60}")
    print("DRY RUN COMPLETE - No changes made")
    print(f"{'='*60}")
    print(f"\nTo perform the actual sync, run:")
    print(f"  python synapse_room_sync.py {input_db_path} {target_db_path} \"{room_id}\"")
    print(f"\n⚠ Remember to backup your target database first!")
    print(f"  cp {target_db_path} {target_db_path}.backup")
    print(f"{'='*60}\n")
    
    input_conn.close()
    target_conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python dry_run_sync.py <input_db> <target_db> <room_id>")
        print("\nExample:")
        print('  python dry_run_sync.py input.db target.db "!abc123:example.com"')
        sys.exit(1)
    
    try:
        dry_run_sync(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"\n\nError during dry run: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
