(define (problem simulation-a)
	(:domain simulation)
	(:objects
		me - person
		living-room - livingroom
		living-room-window - window
		living-room-shelf - shelf
		living-room-tv - tv
		living-room-table - table
		living-room-overhead-light - light
		kitchen - kitchen
		kitchen-sink - sink
		kitchen-fridge - fridge
		kitchen-overhead-light - light
		mark-bedroom - bedroom
		mark-bedroom-window - window
		mark-bedroom-shelf - shelf
		mark-bedroom-table - table
		mark-bedroom-tv - tv
		mark-bedroom-overhead-light - light
		linda-bedroom - bedroom
		linda-bedroom-shelf - shelf
		linda-bedroom-tv - tv
		linda-bedroom-table - table
		linda-bedroom-overhead-light - light
		linda-bedroom-window - window
		fork - fork
		bowl - bowl
		of-mice-and-men-book - book
		apple - apple
		orange - orange
		knife - knife
		purple-pen - pen
		black-pen - pen
		tom-sawyer-book - book
		plate - plate
		spoon - spoon
		lord-of-the-rings-book - book
		blue-pen - pen
		the-discovery-channel - channel
		cartoon-network - channel
		nbc - channel
		cnn - channel
		fox-news - channel
		espn - channel
		level-1 - level
		level-2 - level
		level-3 - level
		level-4 - level
		level-5 - level
		level-6 - level
		level-7 - level
		level-8 - level
		level-9 - level
		level-10 - level
	)
	(:init
		(in-livingroom living-room living-room-window)
		(window-open living-room-window)
		(in-livingroom living-room living-room-shelf)
		(shelf-has-level living-room-shelf level-1)
		(shelf-has-level living-room-shelf level-2)
		(shelf-has-level living-room-shelf level-3)
		(shelf-has-level living-room-shelf level-4)
		(in-livingroom living-room living-room-tv)
		(tv-on living-room-tv)
		(tv-playing-channel living-room-tv nbc)
		(in-livingroom living-room living-room-table)
		(in-livingroom living-room living-room-overhead-light)
		(light-on living-room-overhead-light)
		(in-kitchen kitchen kitchen-sink)
		(faucet-on kitchen-sink)
		(in-kitchen kitchen kitchen-fridge)
		(in-kitchen kitchen kitchen-overhead-light)
		(light-on kitchen-overhead-light)
		(in-bedroom mark-bedroom mark-bedroom-window)
		(in-bedroom mark-bedroom mark-bedroom-shelf)
		(shelf-has-level mark-bedroom-shelf level-1)
		(shelf-has-level mark-bedroom-shelf level-2)
		(shelf-has-level mark-bedroom-shelf level-3)
		(shelf-has-level mark-bedroom-shelf level-4)
		(shelf-has-level mark-bedroom-shelf level-5)
		(shelf-has-level mark-bedroom-shelf level-6)
		(shelf-has-level mark-bedroom-shelf level-7)
		(shelf-has-level mark-bedroom-shelf level-8)
		(shelf-has-level mark-bedroom-shelf level-9)
		(shelf-has-level mark-bedroom-shelf level-10)
		(in-bedroom mark-bedroom mark-bedroom-table)
		(in-bedroom mark-bedroom mark-bedroom-tv)
		(tv-on mark-bedroom-tv)
		(tv-playing-channel mark-bedroom-tv the-discovery-channel)
		(in-bedroom mark-bedroom mark-bedroom-overhead-light)
		(in-bedroom linda-bedroom linda-bedroom-shelf)
		(shelf-has-level linda-bedroom-shelf level-1)
		(shelf-has-level linda-bedroom-shelf level-2)
		(shelf-has-level linda-bedroom-shelf level-3)
		(shelf-has-level linda-bedroom-shelf level-4)
		(shelf-has-level linda-bedroom-shelf level-5)
		(shelf-has-level linda-bedroom-shelf level-6)
		(shelf-has-level linda-bedroom-shelf level-7)
		(shelf-has-level linda-bedroom-shelf level-8)
		(shelf-has-level linda-bedroom-shelf level-9)
		(shelf-has-level linda-bedroom-shelf level-10)
		(in-bedroom linda-bedroom linda-bedroom-tv)
		(tv-on linda-bedroom-tv)
		(tv-playing-channel linda-bedroom-tv fox-news)
		(in-bedroom linda-bedroom linda-bedroom-table)
		(in-bedroom linda-bedroom linda-bedroom-overhead-light)
		(in-bedroom linda-bedroom linda-bedroom-window)
		(in-hand me fork)
		(table-contains mark-bedroom-table bowl)
		(shelf-contains linda-bedroom-shelf of-mice-and-men-book level-4)
		(shelf-contains mark-bedroom-shelf apple level-2)
		(table-contains mark-bedroom-table orange)
		(table-contains mark-bedroom-table knife)
		(table-contains linda-bedroom-table purple-pen)
		(table-contains mark-bedroom-table black-pen)
		(table-contains living-room-table tom-sawyer-book)
		(sink-contains kitchen-sink plate)
		(table-contains mark-bedroom-table spoon)
		(table-contains mark-bedroom-table lord-of-the-rings-book)
		(shelf-contains living-room-shelf blue-pen level-3)
	)
)
