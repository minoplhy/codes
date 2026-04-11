#!/usr/bin/env python3
"""
Matrix Synapse Room Sync Script
Synchronizes events from one SQLite database to another for a specific room.
Handles stream_ordering adjustment to maintain sequential ordering in target DB.
"""

import sqlite3
import sys
from typing import Optional, Tuple


class SynapseRoomSync:
    def __init__(self, input_db_path: str, target_db_path: str, room_id: str):
        self.input_db_path = input_db_path
        self.target_db_path = target_db_path
        self.room_id = room_id
        self.input_conn: Optional[sqlite3.Connection] = None
        self.target_conn: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Connect to both databases"""
        print(f"Connecting to input DB: {self.input_db_path}")
        self.input_conn = sqlite3.connect(self.input_db_path)
        self.input_conn.row_factory = sqlite3.Row
        
        print(f"Connecting to target DB: {self.target_db_path}")
        self.target_conn = sqlite3.connect(self.target_db_path)
        self.target_conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connections"""
        if self.input_conn:
            self.input_conn.close()
        if self.target_conn:
            self.target_conn.close()
            
    def get_max_stream_ordering(self) -> int:
        """Get the maximum stream_ordering from target DB events table"""
        cursor = self.target_conn.cursor()
        cursor.execute("SELECT MAX(stream_ordering) as max_order FROM events")
        result = cursor.fetchone()
        max_order = result['max_order'] if result['max_order'] is not None else 0
        print(f"Current max stream_ordering in target DB: {max_order}")
        return max_order
    
    def get_existing_topological_orderings(self) -> set:
        """Get all existing topological_ordering values for the room in target DB"""
        cursor = self.target_conn.cursor()
        cursor.execute(
            "SELECT topological_ordering FROM events WHERE room_id = ?",
            (self.room_id,)
        )
        existing = {row['topological_ordering'] for row in cursor.fetchall()}
        print(f"Found {len(existing)} existing events in target DB for room {self.room_id}")
        return existing
    
    def get_input_events(self):
        """Get all events from input DB for the specified room, ordered by topological_ordering"""
        cursor = self.input_conn.cursor()
        cursor.execute(
            """
            SELECT * FROM events 
            WHERE room_id = ? 
            ORDER BY topological_ordering ASC
            """,
            (self.room_id,)
        )
        events = cursor.fetchall()
        print(f"Found {len(events)} events in input DB for room {self.room_id}")
        return events
    
    def get_event_json(self, event_id: str, from_input: bool = True) -> Optional[sqlite3.Row]:
        """Get event_json entry for a given event_id"""
        conn = self.input_conn if from_input else self.target_conn
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM event_json WHERE event_id = ?",
            (event_id,)
        )
        return cursor.fetchone()
    
    def copy_event(self, event: sqlite3.Row, new_stream_ordering: int):
        """Copy event to target DB with adjusted stream_ordering"""
        cursor = self.target_conn.cursor()
        
        # Get column names from the event
        columns = event.keys()
        
        # Prepare values, replacing stream_ordering
        values = []
        cols_to_insert = []
        
        for col in columns:
            if col == 'stream_ordering':
                values.append(new_stream_ordering)
            else:
                values.append(event[col])
            cols_to_insert.append(col)
        
        # Build INSERT query
        placeholders = ','.join(['?' for _ in cols_to_insert])
        cols_str = ','.join(cols_to_insert)
        
        insert_query = f"INSERT INTO events ({cols_str}) VALUES ({placeholders})"
        
        try:
            cursor.execute(insert_query, values)
            print(f"  ✓ Copied event {event['event_id'][:20]}... with stream_ordering={new_stream_ordering}")
        except sqlite3.IntegrityError as e:
            print(f"  ✗ Failed to copy event {event['event_id'][:20]}...: {e}")
            raise
    
    def copy_event_json(self, event_id: str):
        """Copy event_json entry for a given event_id"""
        event_json = self.get_event_json(event_id, from_input=True)
        
        if not event_json:
            print(f"  ⚠ No event_json found for event_id: {event_id}")
            return
        
        cursor = self.target_conn.cursor()
        columns = event_json.keys()
        cols_str = ','.join(columns)
        placeholders = ','.join(['?' for _ in columns])
        
        insert_query = f"INSERT OR REPLACE INTO event_json ({cols_str}) VALUES ({placeholders})"
        
        try:
            cursor.execute(insert_query, [event_json[col] for col in columns])
            print(f"  ✓ Copied event_json for {event_id[:20]}...")
        except sqlite3.IntegrityError as e:
            print(f"  ✗ Failed to copy event_json: {e}")
            raise
    
    def copy_related_table(self, table_name: str, event_id: str, id_column: str = "event_id"):
        """
        Copy rows from a related table for a given event_id
        
        Args:
            table_name: Name of the table to copy from
            event_id: The event_id to filter by
            id_column: The column name that contains the event_id (default: "event_id")
        """
        # First check if the table exists
        input_cursor = self.input_conn.cursor()
        input_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not input_cursor.fetchone():
            print(f"  ⚠ Table {table_name} does not exist in input DB, skipping")
            return
        
        # Get rows from input DB
        input_cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (event_id,))
        rows = input_cursor.fetchall()
        
        if not rows:
            # This is normal - not all events have entries in all tables
            return
        
        target_cursor = self.target_conn.cursor()
        
        for row in rows:
            columns = row.keys()
            cols_str = ','.join(columns)
            placeholders = ','.join(['?' for _ in columns])
            
            # Use INSERT OR REPLACE to handle duplicates
            insert_query = f"INSERT OR REPLACE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
            
            try:
                target_cursor.execute(insert_query, [row[col] for col in columns])
            except sqlite3.IntegrityError as e:
                print(f"  ⚠ Failed to copy {table_name} row: {e}")
                # Don't raise - this might be a foreign key issue, continue with other data
            except sqlite3.OperationalError as e:
                print(f"  ⚠ Table {table_name} might not exist in target DB: {e}")
                return
        
        if len(rows) > 0:
            print(f"  ✓ Copied {len(rows)} row(s) from {table_name}")
    
    def copy_event_edges(self, event_id: str):
        """Copy event_edges entries for a given event_id"""
        # event_edges stores the DAG structure
        # We need to copy rows where this event is either the event_id or prev_event_id
        
        input_cursor = self.input_conn.cursor()
        
        # Check if table exists
        input_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='event_edges'"
        )
        if not input_cursor.fetchone():
            return
        
        # Get rows where this event is the event_id
        input_cursor.execute("SELECT * FROM event_edges WHERE event_id = ?", (event_id,))
        rows = input_cursor.fetchall()
        
        if not rows:
            return
        
        target_cursor = self.target_conn.cursor()
        copied = 0
        
        for row in rows:
            columns = row.keys()
            cols_str = ','.join(columns)
            placeholders = ','.join(['?' for _ in columns])
            
            insert_query = f"INSERT OR REPLACE INTO event_edges ({cols_str}) VALUES ({placeholders})"
            
            try:
                target_cursor.execute(insert_query, [row[col] for col in columns])
                copied += 1
            except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
                # Foreign key constraint might fail if prev_event doesn't exist yet
                # This is okay - we'll get it when syncing that event
                pass
        
        if copied > 0:
            print(f"  ✓ Copied {copied} row(s) from event_edges")
    
    def sync_room(self):
        """Main sync logic"""
        print(f"\n{'='*60}")
        print(f"Starting sync for room: {self.room_id}")
        print(f"{'='*60}\n")
        
        # Get existing topological orderings in target
        existing_topological = self.get_existing_topological_orderings()
        
        # Get all events from input DB
        input_events = self.get_input_events()
        
        if not input_events:
            print("No events found in input DB for this room!")
            return
        
        # Get current max stream_ordering
        current_stream_ordering = self.get_max_stream_ordering()
        
        copied_count = 0
        skipped_count = 0
        
        print(f"\n{'='*60}")
        print("Processing events...")
        print(f"{'='*60}\n")
        
        for event in input_events:
            topological_ordering = event['topological_ordering']
            event_id = event['event_id']
            
            # Check if this topological_ordering already exists in target
            if topological_ordering in existing_topological:
                print(f"⊘ Skipping event {event_id[:20]}... (topological_ordering={topological_ordering} already exists)")
                skipped_count += 1
                continue
            
            # Increment stream_ordering for new event
            current_stream_ordering += 1
            
            print(f"\n→ Copying event {event_id[:20]}... (topological_ordering={topological_ordering})")

            try:
                # Copy event with new stream_ordering
                self.copy_event(event, current_stream_ordering)

                # Copy corresponding event_json
                self.copy_event_json(event_id)

                # Copy event_edges (DAG structure)
                self.copy_event_edges(event_id)

                # Copy event_auth (authentication chain)
                self.copy_related_table("event_auth", event_id, "event_id")

                # Copy state_events (if this is a state event)
                self.copy_related_table("state_events", event_id, "event_id")

                self.copy_related_table("event_to_state_groups", event_id, "event_id")

                # Copy event_search_content (full-text search index)
                self.copy_related_table("event_search", event_id, "event_id")

                copied_count += 1
  
            except Exception as e:
                print(f"  ✗ Error copying event: {e}")
                print("  Rolling back transaction...")
                self.target_conn.rollback()
                raise

        # Commit all changes
        print(f"\n{'='*60}")
        print("Committing changes...")
        self.target_conn.commit()

        print(f"\n{'='*60}")
        print("SYNC COMPLETE")
        print(f"{'='*60}")
        print(f"Events copied: {copied_count}")
        print(f"Events skipped: {skipped_count}")
        print(f"Total events processed: {len(input_events)}")
        print(f"Final stream_ordering: {current_stream_ordering}")
        print(f"{'='*60}\n")


def main():
    if len(sys.argv) != 4:
        print("Usage: python synapse_room_sync.py <input_db> <target_db> <room_id>")
        print("\nExample:")
        print('  python synapse_room_sync.py input.db target.db "!abc123:example.com"')
        sys.exit(1)

    input_db = sys.argv[1]
    target_db = sys.argv[2]
    room_id = sys.argv[3]

    syncer = SynapseRoomSync(input_db, target_db, room_id)

    try:
        syncer.connect()
        syncer.sync_room()
    except KeyboardInterrupt:
        print("\n\nSync interrupted by user!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        syncer.close()
        print("Database connections closed.")


if __name__ == "__main__":
    main()
