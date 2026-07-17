using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using VedAstro.Library;

var assembly = typeof(GeoLocation).Assembly;
var methods = assembly.GetTypes()
    .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static))
    .Select(method => method.Name).Distinct().OrderBy(name => name).ToArray();
var methodContracts = assembly.GetTypes()
    .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static))
    .Where(method => method.Name.Contains("Longitude") || method.Name.Contains("Shadbala") || method.Name.Contains("Rasi"))
    .Select(method => new { declaring_type = method.DeclaringType?.FullName, name = method.Name, returns = method.ReturnType.FullName, parameters = method.GetParameters().Select(parameter => new { parameter.Name, type = parameter.ParameterType.FullName }).ToArray() })
    .OrderBy(method => method.name).ToArray();
Console.WriteLine(JsonSerializer.Serialize(new {
    package = "VedAstro.Library",
    version = assembly.GetName().Version?.ToString(),
    informational_version = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion,
    methods = methods.Where(name => name.Contains("Longitude") || name.Contains("Shadbala") || name.Contains("Ashtakavarga") || name.Contains("Rasi")).ToArray(),
    method_contracts = methodContracts
}));
