xfocus= {}

xfocus.calibrationMenu= menu.new
	{
		parent= "Focus",
		name= "XFocus Lens Calibration",
		help= "Calculates & stores lens calibration data for later use by XFocus.",
		depends_on= DEPENDS_ON.AUTOFOCUS | DEPENDS_ON.LIVEVIEW,
		submenu=
			{
				{
					name= "Run",
					help= "Run calibration now (process may take a few minutes).",
					icon_type= ICON_TYPE.ACTION,
					value= " ",
					update= "",
					select=
						function(this)
							task.create(xfocus.runCalibration)
						end
				},
				{
					name= "Start logging",
					icon_type= ICON_TYPE.ACTION,
					value= " ",
					update= "",
					select=
						function(this)
							task.create(xfocus.toggleCalibrationLogging)
						end
				},
				{
					name= "Store by lens",
					help= "Saves the calibration data in a file specific to each lens.",
					icon_type= ICON_TYPE.BOOL,
					choices= { "No", "Yes" },
					value= "Yes"
				},
				{
					name= "Keep focus",
					help= "Returns the lens to its original focus distance after completion.",
					icon_type= ICON_TYPE.BOOL,
					choices= { "No", "Yes" },
					value= "Yes"
				}
			}
	}

function xfocus:runCalibration()
	
	local stop

	local currPosition
	local positionStr

	local currFocus
	local focusStr

	local stepStr
	local userStep= 1

	while lens.focus(1, 3, true, 200) == true  -- makes sure the lens is at the starting point
	do userStep= userStep + 1 end

	local lensID= lens.name:upper():gsub("EF", ""):gsub("%W", ""):gsub("ISUSM", "-IU"):gsub("IS", "-I"):gsub("USM", "-U"):gsub("[^%dFIU-]", ""):sub(1, 8)
	local log= io.open( (  ( xfocus.calibrationMenu.submenu["Store by lens"].value=="Yes" and lensID )  or  "xfocus"  ) .. ".lns", "a" )

	local date= dryos.date
	date= string.format("%d/%02d/%d %02d:%02d", date.month, date.day, date.year, date.hour, date.min)

	log:write("***XFocus Calibration Results***\r\n")
	log:write("***Lens: " .. lens.name .. "\r\n")
	log:write("***Date: " .. date .. "\r\n")

	local maxSteps
	local currStep= 0
	log:write("\r\nLarge Steps...\r\n")
	repeat
		stop=  lens.focus(-1, 3, true, 200) ~= true
		currStep= currStep+1
		stepStr= (  ( currStep<10 and "   " )  or  ( currStep<100 and "  " )  or  ( currStep<1000 and " " or "" )  ) .. currStep
		currFocus= lens.focus_distance/10
		focusStr= (  ( currFocus<10 and "    " )  or  ( currFocus<100 and "   " )  or  ( currFocus<1000 and "  " )  or  ( currFocus<10000 and " " or "" )  ) .. currFocus
		currPosition= lens.focus_pos
		if currPosition ~= nil then
			positionStr= (  ( currPosition<10 and "   " )  or  ( currPosition<100 and "  " )  or  ( currPosition<1000 and " " or "" )  ) .. currPosition
			log:write(stepStr .. ": " .. focusStr .. "cm  @  " .. positionStr .. "\r\n")
		else
			log:write(stepStr .. ": " .. focusStr .. "cm\r\n")
		end
	until stop==true
	maxSteps= currStep+1

	currStep= 0
	lens.focus(maxSteps, 3, true, 200)
	log:write("\r\nMedium Steps...\r\n")
	repeat
		stop=  lens.focus(-1, 2, true, 200) ~= true
		currStep= currStep+1
		stepStr= (  ( currStep<10 and "   " )  or  ( currStep<100 and "  " )  or  ( currStep<1000 and " " or "" )  ) .. currStep
		currFocus= lens.focus_distance/10
		focusStr= (  ( currFocus<10 and "    " )  or  ( currFocus<100 and "   " )  or  ( currFocus<1000 and "  " )  or  ( currFocus<10000 and " " or "" )  ) .. currFocus
		currPosition= lens.focus_pos
		if currPosition ~= nil then
			positionStr= (  ( currPosition<10 and "   " )  or  ( currPosition<100 and "  " )  or  ( currPosition<1000 and " " or "" )  ) .. currPosition
			log:write(stepStr .. ": " .. focusStr .. "cm  @  " .. positionStr .. "\r\n")
		else
			log:write(stepStr .. ": " .. focusStr .. "cm\r\n")
		end
	until stop==true

	currStep= 0
	lens.focus(maxSteps, 3, true, 200)
	log:write("\r\nSmall Steps...\r\n")
	repeat
		stop=  lens.focus(-1, 1, true, 200) ~= true
		currStep= currStep+1
		stepStr= (  ( currStep<10 and "   " )  or  ( currStep<100 and "  " )  or  ( currStep<1000 and " " or "" )  ) .. currStep
		currFocus= lens.focus_distance/10
		focusStr= (  ( currFocus<10 and "    " )  or  ( currFocus<100 and "   " )  or  ( currFocus<1000 and "  " )  or  ( currFocus<10000 and " " or "" )  ) .. currFocus
		currPosition= lens.focus_pos
		if currPosition ~= nil then
			positionStr= (  ( currPosition<10 and "   " )  or  ( currPosition<100 and "  " )  or  ( currPosition<1000 and " " or "" )  ) .. currPosition
			log:write(stepStr .. ": " .. focusStr .. "cm  @  " .. positionStr .. "\r\n")
		else
			log:write(stepStr .. ": " .. focusStr .. "cm\r\n")
		end
	until stop==true

	log:write("\r\n\r\n")
	log:close()

	if xfocus.calibrationMenu.submenu["Keep focus"].value=="Yes" then
		lens.focus(maxSteps-userStep, 3, true, 200)  -- returns to the original focus distance
	end

end

function xfocus:toggleCalibrationLogging()

	if xfocus.lastCalibrationLog then
		
		xfocus.lastCalibrationLog:write("\r\n\r\n")
		xfocus.lastCalibrationLog:close()
		xfocus.lastCalibrationLog= nil
		xfocus.calibrationMenu.submenu["Start logging"].name= "Start logging"

	else

		local lensID= lens.name:upper():gsub("EF", ""):gsub("%W", ""):gsub("ISUSM", "-IU"):gsub("IS", "-I"):gsub("USM", "-U"):gsub("[^%dFIU-]", ""):sub(1, 8)
		local log= io.open( (  ( xfocus.calibrationMenu.submenu["Store by lens"].value=="Yes" and lensID )  or  "xfocus"  ) .. ".lns", "a" )
		xfocus.calibrationMenu.submenu["Start logging"].name= "End logging"

		local date= dryos.date
		date= string.format("%d/%02d/%d %02d:%02d", date.month, date.day, date.year, date.hour, date.min)
		xfocus.lastCalibrationLog= log

		log:write("***XFocus Calibration Results***\r\n")
		log:write("***Lens: " .. lens.name .. "\r\n")
		log:write("***Date: " .. date .. "\r\n")

	end

end

function tostring_recursive(obj, indent)
	local strVal= tostring(obj)
    if type(obj) ~= "table" then
        obj= getmetatable(obj)
    end
    if type(obj) == "table" then
		if indent == nil then
			indent= "\r\n\t"
		end
        for prop, val in pairs(obj) do
            if prop ~= "__index" then
                strVal= strVal .. indent .. tostring(prop) .. ": " .. tostring_recursive(val, indent.."\t")
            end
        end
    end
	return strVal
end

--[[
	function property.LV_LENS:handler(value)
		if xfocus.lastCalibrationLog then
			xfocus.lastCalibrationLog:write( "LV_LENS: " .. tostring_recursive(value) .. "\r\n" )
		end
	end
]]--

function property.LV_FOCUS:handler(value)
	if xfocus.lastCalibrationLog then
		xfocus.lastCalibrationLog:write( "LV_FOCUS: " .. tostring_recursive(value) .. "\r\n" )
	end
end

function property.LV_FOCUS_DONE:handler(value)
	if xfocus.lastCalibrationLog then
		xfocus.lastCalibrationLog:write( "LV_FOCUS_DONE: " .. tostring_recursive(value) .. "\r\n" )
	end
end