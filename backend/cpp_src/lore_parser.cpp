#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <map>
#include <regex>
#include <algorithm>
#include <iostream>

namespace py = pybind11;

// Map from lore name to internal name
std::map<std::string, std::string> STAT_NAME_MAP = {
    {"health", "health"},
    {"defense", "defense"},
    {"strength", "strength"},
    {"speed", "speed"},
    {"crit chance", "crit_chance"},
    {"crit damage", "crit_damage"},
    {"intelligence", "intelligence"},
    {"attack speed", "bonus_attack_speed"},
    {"bonus attack speed", "bonus_attack_speed"},
    {"ferocity", "ferocity"},
    {"magic find", "magic_find"},
    {"true defense", "true_defense"},
    {"sea creature chance", "sea_creature_chance"},
    {"trophy fish chance", "trophy_fish_chance"},
    {"treasure chance", "treasure_chance"},
    {"farming fortune", "farming_fortune"},
    {"foraging fortune", "foraging_fortune"},
    {"mining fortune", "mining_fortune"},
    {"mining speed", "mining_speed"},
    {"fishing speed", "fishing_speed"},
    {"pet luck", "pet_luck"},
    {"ability damage", "ability_damage"},
    {"vitality", "vitality"},
    {"mending", "mending"},
    {"health regen", "health_regen"},
    {"damage", "damage"},
    {"swing range", "swing_range"},
    {"sweep", "sweep"}
};

// Regex for color codes: §[0-9a-fk-or]
std::regex COLOR_CODE_REGEX("§[0-9a-fk-or]", std::regex_constants::icase);

// Regex for stat line: ^([A-Za-z ]+):\s*([+-]?\d+(?:\.\d+)?)
std::regex STAT_LINE_REGEX("^([A-Za-z ]+):\\s*([+-]?\\d+(?:\\.\\d+)?)");

std::map<std::string, double> parse_lore_stats(const std::vector<std::string>& lore_lines) {
    std::map<std::string, double> stats;

    for (const auto& line : lore_lines) {
        // Remove color codes
        std::string clean_line = std::regex_replace(line, COLOR_CODE_REGEX, "");
        
        // Trim (simple version)
        clean_line.erase(0, clean_line.find_first_not_of(" \t\r\n"));
        clean_line.erase(clean_line.find_last_not_of(" \t\r\n") + 1);

        if (clean_line.empty() || clean_line[0] == '[') {
            continue;
        }

        std::smatch match;
        if (std::regex_search(clean_line, match, STAT_LINE_REGEX)) {
            std::string stat_name = match[1].str();
            std::string stat_value_str = match[2].str();

            // Lowercase stat name
            std::transform(stat_name.begin(), stat_name.end(), stat_name.begin(), ::tolower);
            
            // Trim stat name
            stat_name.erase(0, stat_name.find_first_not_of(" \t\r\n"));
            stat_name.erase(stat_name.find_last_not_of(" \t\r\n") + 1);

            auto it = STAT_NAME_MAP.find(stat_name);
            if (it != STAT_NAME_MAP.end()) {
                try {
                    double value = std::stod(stat_value_str);
                    stats[it->second] = value;
                } catch (...) {
                    continue;
                }
            }
        }
    }
    return stats;
}

bool is_soulbound(const std::vector<std::string>& lore, const std::vector<std::string>& lore_colored) {
    // Check colored lore first
    for (const auto& line : lore_colored) {
        if (line.find("Soulbound") != std::string::npos || line.find("SOULBOUND") != std::string::npos) {
            return true;
        }
    }

    // Check plain lore
    for (const auto& line : lore) {
        std::string line_upper = line;
        std::transform(line_upper.begin(), line_upper.end(), line_upper.begin(), ::toupper);
        if (line_upper.find("SOULBOUND") != std::string::npos || line_upper.find("CO-OP SOULBOUND") != std::string::npos) {
            return true;
        }
    }

    return false;
}

PYBIND11_MODULE(altsky_cpp, m) {
    m.doc() = "Altsky C++ optimization module";
    m.def("parse_lore_stats", &parse_lore_stats, "Parse stats from item lore");
    m.def("is_soulbound", &is_soulbound, "Check if item is soulbound based on lore");
}
