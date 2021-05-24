import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.json.JSONArray;
import org.json.JSONObject;

public class DotaConstants {
    private static DotaConstants instance = null;
    private JSONObject clusters;
    private JSONObject regions;
    private JSONArray versions;

    private DotaConstants() {
        try {
            String clustersString = new String(Files.readAllBytes(Paths.get("clusters.json")), StandardCharsets.UTF_8);
            clusters = new JSONObject(clustersString);
            String regionsString = new String(Files.readAllBytes(Paths.get("regions.json")), StandardCharsets.UTF_8);
            regions = new JSONObject(regionsString);
            String versionsString = new String(Files.readAllBytes(Paths.get("versions.json")), StandardCharsets.UTF_8);
            versions = new JSONArray(versionsString);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static String getRegion(int code) {
        if (instance == null) {
            instance = new DotaConstants();
        }
        String clusterKey = String.valueOf(code);
        String regionKey = "0";
        if (!instance.clusters.isNull(clusterKey)) {
            regionKey = instance.clusters.getString(clusterKey);
        }
        JSONObject region = instance.regions.getJSONObject(regionKey);
        return String.format("%s,%s", region.getString("latitude"), region.getString("longitude"));
    }

    public static String getVersion(long unixTimestamp) {
        if (instance == null) {
            instance = new DotaConstants();
        }
        for (int i = instance.versions.length() - 1; i >= 0; i--) {
            long timestamp = instance.versions.getJSONObject(i).getLong("timestamp");
            if (timestamp < unixTimestamp) {
                return instance.versions.getJSONObject(i).getString("name");
            }
        }
        return "version_not_found";
    }
}
