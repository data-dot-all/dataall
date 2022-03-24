package com.aws.athena.udf.h3;

import com.amazonaws.athena.connector.lambda.handlers.UserDefinedFunctionHandler;
import com.uber.h3core.AreaUnit;
import com.uber.h3core.H3Core;
import com.uber.h3core.LengthUnit;
import com.uber.h3core.exceptions.DistanceUndefinedException;
import com.uber.h3core.exceptions.LineUndefinedException;
import com.uber.h3core.exceptions.PentagonEncounteredException;
import com.uber.h3core.util.GeoCoord;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import java.util.stream.Stream;

public class H3AthenaHandler extends UserDefinedFunctionHandler {

    private final H3Core h3Core;
    private static final String SOURCE_TYPE = "h3_athena_udf_handler";

    public H3AthenaHandler() throws IOException {
        super(SOURCE_TYPE);
        this.h3Core = H3Core.newInstance();
    }

    /** Indexes the location at the specified reolution, returnin index of the cell as number containing
     *  the location.
     *   @param lat the latitude of the location
     *   @param lng the longitude of the location
     *   @param res the resolution 0 &lt;= res &lt;= 15
     *   @return The H3 index as a long. Null when one of the parameter is null.
     *   @throws IllegalArgumentException latitude, longitude, or resolution are out of range.
     */
    public Long geoToH3(Double lat, Double lng, Integer res) {
        if (lat == null || lng == null || res == null) {
            return null;
        }
        return h3Core.geoToH3(lat, lng, res);
    }

    /** Indexes the location at the specified reolution, returning index of the cell as String containing
     *  the location.
     *   @param lat the latitude of the location
     *   @param lng the longitude of the location
     *   @param res the resolution 0 &lt;= res &lt;= 15
     *   @return The H3 index as a long. Null when one of the parameter is null.
     *   @throws IllegalArgumentException latitude, longitude, or resolution are out of range.
     */
    public String geoToH3Address(Double lat, Double lng, Integer res) {
        if (lat == null || lng == null || res == null) {
            return null;
        }
        return h3Core.geoToH3Address(lat, lng, res);
    }

    /** Finds the centroid of an index, and returns an array list of coordinates representing latitude and longitude 
     *  respectively.
     *  @param h3 the H3 index
     *  @return List of Double of size 2 representing latitude and longitude. Null when the index is null.
     *  @throws IllegalArgumentException when the index is out of range
     */
    public List<Double> h3ToGeo(Long h3) {
        if (h3 == null) {
            return null;
        }
        GeoCoord coord = h3Core.h3ToGeo(h3);
        return new ArrayList<Double>(Arrays. asList(coord.lat, coord.lng));
    }

    /** Finds the centroid of an index, and returns a WKT of the centroid.
     *  @param h3 the H3 index
     *  @return the WKT of the centroid of an H3 index. Null when the index is null;
     *  @throws IllegalArgumentException when the index is out of range
     */
    public String h3ToGeoWKT(Long h3) {
        if (h3 == null) {
            return null;
        }
        GeoCoord coord = h3Core.h3ToGeo(h3);
        return wktPoint(coord);
    }

     /** Finds the centroid of an index, and returns an array list of coordinates representing latitude and longitude 
     *  respectively.
     *  @param h3Address the H3 index in its string form
     *  @return List of Double of size 2 representing latitude and longitude. Null when the address is null
     *  @throws IllegalArgumentException when the address is out of range
     */
    public List<Double> h3ToGeo(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return pointsList(h3Core.h3ToGeo(h3Address));
    }

    /** Finds the centroid of an index, and returns a WKT of the centroid.
     *  @param h3Address the H3 index in its string form
     *  @return the WKT of the centroid of an H3 index. Null when the address is null.
     *  @throws IllegalArgumentException  when address is out of range 
     */
    public String h3ToGeoWKT(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return  wktPoint(h3Core.h3ToGeo(h3Address));
    }

    /** Finds the boundary of an H3 index.
     * @param h3 the H3 index
     * @return the list of points representing the points in the boundary. Each returned list consists of two members, the first one is latitude, and the 
     * second one is longitude. Null when the parameter is null.
     * @throws IllegalArgumentException  when address is out of range 
     */
    public List<List<Double>> h3ToGeoBoundary(Long h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.h3ToGeoBoundary(h3).stream()
                .map(H3AthenaHandler::pointsList)
                .collect(Collectors.toList());
    }

    /** Finds the boundary of an H3 index.
     * @param h3 the H3 index
     * @return the list of points representing the points in the boundary. Each returned list consists of a WKT representation of the point.
     * Null when h3 is null.
     * @throws IllegalArgumentException  when address is out of range.
     */
    public List<String> h3ToGeoBoundaryWKT(Long h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.h3ToGeoBoundary(h3).stream()
                .map(H3AthenaHandler::wktPoint)
                .collect(Collectors.toList());

    }

    
    /** Finds the boundary of an H3 index in a string form.
     * @param h3Address the H3 index
     * @return the list of points representing the points in the boundary. Each returned list consists of two members, the first one is latitude, and the 
     * second one is longitude . Null when the h3Address is null.
     * @throws IllegalArgumentException  when address is out of range.
     */
    public List<String> h3ToGeoBoundaryWKT(String h3Address){
        if (h3Address == null) {
           return null;
        }
        return h3Core.h3ToGeoBoundary(h3Address).stream()
                .map(H3AthenaHandler::wktPoint)
                .collect(Collectors.toList());
    
    }
    
    /** Finds the boundary of an H3 index in a string form
     * @param h3Address the H3 index 
     * @return the list of points representing the points in the boundary. Each returned list consists of a WKT representation of the point.
     * Null when h3Address is null.
     * @throws IllegalArgumentException  when address is out of range. 
     */
    public List<List<Double>> h3ToGeoBoundary(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return h3Core.h3ToGeoBoundary(h3Address).stream()
                .map(H3AthenaHandler::pointsList)
                .collect(Collectors.toList());
    }

    /** Returns the resolution of an index.
     *  @param h3 the H3 index.
     *  @return the resolution. Null when h3 is null.
     *  @throws  IllegalArgumentException  when index is out of range.
     */
    public Integer h3GetResolution(Long h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.h3GetResolution(h3);
    }


    /** Returns the resolution of an index.
     *  @param h3Address the H3 index in string form.
     *  @return the resolution. Null when h3Address is null.
     */
    public Integer h3GetResolution(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return h3Core.h3GetResolution(h3Address);
    }

    /** Returns the base cell number of the index.
     * @param h3 the index. 
     * @return the base cell number of the index. Null when h3 is null.
     */
    public Integer h3GetBaseCell(Long h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.h3GetBaseCell(h3);

    }

    /** Returns the base cell number of the index in string form
     * @param h3Address the address. 
     * @return the base cell number of the index. Null when h3Address is null.
     * @throws IllegalArgumentException when index is out of range.
     */
    public Integer h3GetBaseCell(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return h3Core.h3GetBaseCell(h3Address);
    }

    /** Converts the string representation to H3Index (uint64_t) representation.
    *   @param h3Address the h3 address.
    *   @return the string representation. Null when h3Address is null.
    */
    public Long stringToH3(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return h3Core.stringToH3(h3Address);
    }

    /** Converts the H3Index representation of the index to the string representation. str must be at least of length 17.
     *  @param the h3 the h3 index.
     *  @return the string representation if the index.
     */
    public String h3ToString(Long h3) {
        if (h3 == null) {
            return null;
        }
        return h3Core.h3ToString(h3);
    }

    public boolean h3IsValid(Long h3) {
        if (h3 == null) {
            return false;
        }

        return h3Core.h3IsValid(h3);
    }

    public boolean h3IsValid(String h3Address){
        if (h3Address == null){
            return false;
        }
        return h3Core.h3IsValid(h3Address);
    }

    public boolean h3IsResClassIII(Long h3){
        if (h3 == null){
            return false;
        }
        return h3Core.h3IsResClassIII(h3);
    }

    public boolean h3IsResClassIII(String h3Address) {
        if (h3Address ==null){
            return false;
        }
        return h3Core.h3IsResClassIII(h3Address);
    }

    public boolean h3IsPentagon(Long h3){
        if (h3 == null) {
            return false;
        }
        return h3Core.h3IsPentagon(h3);
    }
    public boolean h3IsPentagon(String h3Address){
        if (h3Address == null) {
            return false;
        }
        return h3Core.h3IsPentagon(h3Address);
    }


    /** Find all icosahedron faces intersected by a given H3 index.*/
    public List<Integer> h3GetFaces(Long h3){
        if (h3 == null) {
            return null;
        }
        return new ArrayList<Integer>(h3Core.h3GetFaces(h3));
    }

    /** Find all icosahedron faces intersected by a given H3 index.*/
    public List<Integer> h3GetFaces(String h3Address){
        if (h3Address == null) {
            return null;
        }
        return new ArrayList<Integer>(h3Core.h3GetFaces(h3Address));
    }

    public List<Long> kRing(Long origin, int k){
        if (origin == null){
            return null;
        }
        return h3Core.kRing(origin, k);

    }

    public List<String> kRing(String origin, int k){
        if (origin == null) {
            return null;
        }
        return h3Core.kRing(origin, k);
    }


    public List<List<Long>> kRingDistances(Long origin, int k) {
        if (origin == null){
            return null;
        }
        return h3Core.kRingDistances(origin, k);

    }
    public List<List<String>> kRingDistances(String origin, int k){
        if (origin == null){
            return null;
        }
        return h3Core.kRingDistances(origin, k);
    }

    public List<List<Long>> hexRange(Long h3, int k) throws PentagonEncounteredException{
        if (h3 == null){
            return null;
        }
        return h3Core.hexRange(h3, k);
    }

    public List<List<String>> hexRange(String h3Address, int k) throws PentagonEncounteredException{
        if (h3Address == null){
            return null;
        }
        return h3Core.hexRange(h3Address, k);
    }


    public List<Long> hexRing(Long h3, int k) throws PentagonEncounteredException{
        if (h3 == null) {
            return null;
        }
        return h3Core.hexRing(h3, k);
    }

    public List<String> hexRing(String h3Address, int k) throws PentagonEncounteredException {
        if (h3Address == null){
            return null;
        }
        return h3Core.hexRing(h3Address, k);
    }


    public List<Long> h3Line(Long start, Long end)  {
        if (start == null || end == null) {
            return null;
        }
        try{
            return h3Core.h3Line(start, end);
        } catch (LineUndefinedException e) {
            return null;
        }

    }
    public List<String> h3Line(String startAddress, String endAddress) throws LineUndefinedException {
        if (startAddress == null || endAddress == null) {
            return null;
        }
        try{
            return h3Core.h3Line(startAddress, endAddress);
        } catch (LineUndefinedException e) {
            return null;
        }
    }


    public Integer h3Distance(Long a, Long b) throws DistanceUndefinedException{
        if (a == null || b == null) {
            return null;
        }
        if (h3Core.h3GetResolution(a) != h3Core.h3GetResolution(b)) {
            throw new IllegalArgumentException("Cannot compute distance of two indexes from different resolutions");
        }
        return h3Core.h3Distance(a, b);
    }

    public Integer h3Distance(String a, String b) throws DistanceUndefinedException {
        if (a == null || b == null) {
            return null;
        }
        if (h3Core.h3GetResolution(a) != h3Core.h3GetResolution(b)) {
            throw new IllegalArgumentException("Cannot compute distance of two indexes from different resolutions");
        }
        return h3Core.h3Distance(a, b);
    }

    /** Returns the parent (coarser) index containing h. */
    public Long h3ToParent(Long h3, int parentRes) {
        if (h3 == null) {
            return null;
        }
        return h3Core.h3ToParent(h3, parentRes);
    }

    /** Returns the parent (coarser) index containing h3Address. */
    public String h3ToParent(String h3Address, int parentRes) {
        if (h3Address == null){
            return null;
        }
        return h3Core.h3ToParentAddress(h3Address, parentRes);
    }

    public List<Long> h3ToChildren(Long h3, int childRes) {
        if (h3 == null){
            return null;
        }
        return h3Core.h3ToChildren(h3, childRes);

    }
    public List<String> h3ToChildren(String h3Address, int childRes) {
        if (h3Address == null) {
            return null;
        }
        return h3Core.h3ToChildren(h3Address, childRes);
    }

    public Long h3ToCenterChild(Long h3, int childRes){
        if (h3 == null){
            return null;
        }
        return h3Core.h3ToCenterChild(h3, childRes);
    }
    public String h3ToCenterChild(String h3Address, int childRes){
        if (h3Address == null)  {
            return null;
        }
        return h3Core.h3ToCenterChild(h3Address, childRes);
    }


    public List<Long> compact(List<Long> h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.compact(h3);
    }
    public List<String> compactAddress(List<String> h3Addresses) {
        if (h3Addresses == null) {
            return null;
        }
        return h3Core.compactAddress(h3Addresses);
    }

    public List<Long> uncompact(List<Long> h3, int res) {
        if (h3 == null) {
            return null;
        }
        return h3Core.uncompact(h3, res);

    }
    public List<String> uncompactAddress(List<String> h3Addresses, int res){
        if (h3Addresses == null) {
            return null;
        }
        return h3Core.uncompactAddress(h3Addresses, res);
    }

    public List<Long> polyfill(List<String> points, List<List<String>> holes, int res) {
        if (points == null) {
            return null;
        }
        if (holes == null) {
            holes = new ArrayList<List<String>>();
        }

        List<GeoCoord> geoCoordPoints =
                points.stream().map(H3AthenaHandler::geoCoordFromWKTPoint).collect(Collectors.toList());
        List<List<GeoCoord>> geoCoordHoles =
                holes.stream()
                        .map(x ->
                                x.stream()
                                .map(H3AthenaHandler::geoCoordFromWKTPoint)
                                .collect(Collectors.toList()))
                        .collect(Collectors.toList());
        return h3Core.polyfill(geoCoordPoints, geoCoordHoles, res);


    }
    
    public List<String> polyfillAddress(List<String> points, List<List<String>> holes, int res) {
        if (points == null) {
            return null;
        }
        if (holes == null) {
            holes = new ArrayList<List<String>>();
        }

        List<GeoCoord> geoCoordPoints =
                points.stream().map(H3AthenaHandler::geoCoordFromWKTPoint).collect(Collectors.toList());
        List<List<GeoCoord>> geoCoordHoles =
                holes.stream()
                        .map(x ->
                                x.stream()
                                .map(H3AthenaHandler::geoCoordFromWKTPoint)
                                .collect(Collectors.toList()))
                        .collect(Collectors.toList());
        return h3Core.polyfillAddress(geoCoordPoints, geoCoordHoles, res);
    }

    public List<List<List<String>>> h3SetToMultiPolygon(List<Long> h3, boolean geoJson) {
        if (h3 == null) {
            return null;
        }
        List<List<List<GeoCoord>>> result = h3Core.h3SetToMultiPolygon(h3, geoJson);
        return result.stream().map(r -> 
                            r.stream().map( polygon -> polygon.stream().map(H3AthenaHandler::wktPoint).
                                                collect(Collectors.toList()))
                                    .collect(Collectors.toList()))
                            .collect(Collectors.toList());
    }

    public List<List<List<String>>> h3AddressSetToMultiPolygon(List<String> h3Addresses, boolean geoJson){
        if (h3Addresses == null){
            return null;
        }
        List<List<List<GeoCoord>>> result = h3Core.h3AddressSetToMultiPolygon(h3Addresses, geoJson);
        return result.stream().map(r -> 
                 r.stream().map( polygon -> polygon.stream().map(H3AthenaHandler::wktPoint).
                                                collect(Collectors.toList()))
                                    .collect(Collectors.toList()))
                            .collect(Collectors.toList());
    }

    public Boolean h3IndexesAreNeighbors(Long origin, Long destination){
        if (origin == null || destination == null ){
            return null;
        }
        return h3Core.h3IndexesAreNeighbors(origin, destination);
    }


    public Boolean h3IndexesAreNeighbors(String origin, String destination){
        if (origin == null || destination == null ){
            return null;
        }
        return h3Core.h3IndexesAreNeighbors(origin, destination);
    }

    public Long getH3UnidirectionalEdge(Long origin, Long destination) {
        if (origin == null || destination == null ){
            return null;
        }
        return h3Core.getH3UnidirectionalEdge(origin, destination);
    }
    public String getH3UnidirectionalEdge(String origin, String destination) {
        if (origin == null || destination == null ){
            return null;
        }
        return h3Core.getH3UnidirectionalEdge(origin, destination);

    }

    public boolean h3UnidirectionalEdgeIsValid(Long edge){
        if (edge == null) {
            return false;
        }
        return h3Core.h3UnidirectionalEdgeIsValid(edge);
    }
    public boolean h3UnidirectionalEdgeIsValid(String edgeAddress){
        if (edgeAddress == null) {
            return false;
        }
        return h3Core.h3UnidirectionalEdgeIsValid(edgeAddress);      
    }

    public Long getOriginH3IndexFromUnidirectionalEdge(Long edge){
        if (edge == null) {
            return null;
        }
        return h3Core.getOriginH3IndexFromUnidirectionalEdge(edge);
    }
    public String getOriginH3IndexFromUnidirectionalEdge(String edgeAddress){
        if (edgeAddress == null){
            return null;
        }
        return h3Core.getOriginH3IndexFromUnidirectionalEdge(edgeAddress);
    }

    public Long getDestinationH3IndexFromUnidirectionalEdge(Long edge){
        if (edge == null) {
            return null;
        }
        return h3Core.getDestinationH3IndexFromUnidirectionalEdge(edge);
    }
    public String getDestinationH3IndexFromUnidirectionalEdge(String edgeAddress){
        if (edgeAddress == null){
            return null;
        }
        return h3Core.getDestinationH3IndexFromUnidirectionalEdge(edgeAddress);
    }

    public List<Long> getH3UnidirectionalEdgesFromHexagon(Long h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.getH3UnidirectionalEdgesFromHexagon(h3);

    }
    public List<String> getH3UnidirectionalEdgesFromHexagon(String h3){
        if (h3 == null) {
            return null;
        }
        return h3Core.getH3UnidirectionalEdgesFromHexagon(h3);
    }

    public List<String> getH3UnidirectionalEdgeBoundary(Long edge){
        if (edge == null) {
            return null;
        }
        return h3Core.getH3UnidirectionalEdgeBoundary(edge).stream()
                .map(H3AthenaHandler::wktPoint)
                .collect(Collectors.toList());
    }
    public List<String> getH3UnidirectionalEdgeBoundary(String edgeAddress){
        if (edgeAddress == null) {
            return null;
        }
        return h3Core.getH3UnidirectionalEdgeBoundary(edgeAddress).stream()
                .map(H3AthenaHandler::wktPoint)
                .collect(Collectors.toList());
    }

    public Double hexArea(int res, String unit) {
        return h3Core.hexArea(res, AreaUnit.valueOf(unit));
    }

    public Double cellArea(Long h3, String unit) {
        if (h3 == null) {
            return null;
        }
        return h3Core.cellArea(h3, AreaUnit.valueOf(unit));
    }

    public Double cellArea(String h3Address, String unit) {
        if (h3Address == null) {
            return null;
        }
        return h3Core.cellArea(h3Address, AreaUnit.valueOf(unit));
    }


    public double edgeLength(int res, String unit){
        return h3Core.edgeLength(res, LengthUnit.valueOf(unit));
    }

    public Double exactEdgeLength(Long h3, String unit){
        if (h3 == null){
            return null;
        }

        return h3Core.exactEdgeLength(h3, LengthUnit.valueOf(unit));
    }

    public long numHexagons(int res){
        return h3Core.numHexagons(res);
    }

    public List<Long> getRes0Indexes(int res){
        return new ArrayList<Long>(h3Core.getRes0Indexes());
    }
    public List<String> getRes0IndexesAddresses(int res){
        return new ArrayList<String>(h3Core.getRes0IndexesAddresses());
    }

    public List<Long> getPentagonIndexes(int res){
        return new ArrayList<Long>(h3Core.getPentagonIndexes(res));
    }
    public List<String> getPentagonIndexesAddresses(int res){
        return new ArrayList<String>(h3Core.getPentagonIndexesAddresses(res));
    }

    public double pointDist(String point1, String point2, String unit){
        return h3Core.pointDist(geoCoordFromWKTPoint(point1), geoCoordFromWKTPoint(point2), LengthUnit.valueOf(unit));
    }


    private static List<String> wktPoints(List<GeoCoord> points){
        return points.stream().map(H3AthenaHandler::wktPoint).collect(Collectors.toList());
    }
    private static List<Double> pointsList(GeoCoord geoCoord) {
        return new ArrayList<Double>(Arrays. asList(geoCoord.lat, geoCoord.lng));
    }

    private static String wktPoint(GeoCoord geoCoord) {
        return String.format("POINT (%f %f)", geoCoord.lng, geoCoord.lat);
    }

    private static GeoCoord geoCoordFromWKTPoint(String wktPoint) {
        
        String trimmed = wktPoint.trim();
        if (trimmed.startsWith("POINT")) {
            String betweenParentheses = trimmed.substring(5, trimmed.length());
            if ( betweenParentheses.charAt(0) == '(' && betweenParentheses.charAt(betweenParentheses.length()-1) == ')' ){
                String[] splitted = betweenParentheses.substring(1, betweenParentheses.length()-1).split("\\s+");
                return new GeoCoord(Double.parseDouble(splitted[0]), Double.parseDouble(splitted[1]));
            }
            else {
                throw new IllegalArgumentException("Cannot find parentheses in String" + wktPoint);
            }
        }
        else {
            throw new IllegalArgumentException("Cannot find POINT" + wktPoint);
        }
    }
}