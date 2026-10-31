local HttpService = game:GetService("HttpService")

-- URL Backend ของเราบน Render
local BACKEND_URL = "https://nine-extractor-backend.onrender.com/deobfuscate"

local function deobfuscateCode(targetLuaCode)
    local requestPayload = HttpService:JSONEncode({ code = targetLuaCode })
    
    local success, response = pcall(function()
        return HttpService:PostAsync(
            BACKEND_URL,
            requestPayload,
            Enum.HttpContentType.ApplicationJson
        )
    end)

    if success then
        local data = HttpService:JSONDecode(response)
        if data.success then
            return data.deobfuscated_code
        end
    end
    return nil
end
