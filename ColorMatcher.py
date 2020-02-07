#!/usr/bin/python
import re
import glob
import json

class ElementList:
  icons = []
  textColors = []
  linkColors = []
  borderColors = []
  backgroundColors = []
  attributedStringColors = []

  def totalElementCount(self):
    return len(self.icons) + len(self.textColors) + len(self.linkColors) + len(self.borderColors) + len(self.backgroundColors) + len(self.attributedStringColors)


class ElementPattern:
  iconPattern = re.compile(r'(.*)(\s*=?\s*)(XOKitIcon.*)')
  iconElementPattern = re.compile(r'(\w+)(.setImage|.image)')
  iconColorPattern = re.compile(r'(tinted\(\s*|color:\s*)(UIColor)?(\.)*(\w+)')
  
  cellPattern = re.compile(r'(class\s*)(\S*)(\s*:.*Cell)')
  controllerPattern = re.compile(r'(class\s*)(\S*)(\s*:\s*XOViewController|UITabBarController|TabbedContainerViewController|XOWebViewController|OnboardingStepViewController|RegistrationChildPageViewController|XOTableViewController|UINavigationViewController|UIPageViewController|XOBaseWebViewController|RegistryBaseViewController|RegistrySectionBaseViewController)')

  textColorPattern = re.compile(r'(\S*textColor\s*=\s*)(UIColor)?(\.)(\w+)')
  linkColorPattern = re.compile(r'(\S*setTitleColor\()(UIColor)?(\.)(\w+)(.*)')
  borderColorPattern = re.compile(r'(\S*borderColor\s*=\s*)(UIColor)?(\.)(\w+)')
  backgroundColorPattern = re.compile(r'(\S*backgroundColor\s*=\s*)(UIColor)?(\.)(\w+)')
  attributedStringColorPattern = re.compile(r'(.*foregroundColor\s*:\s*)(UIColor)?(\.)(\w+)(.*)')

class ColorMapping:
  data = dict()

  def __init__(self):
    with open('/Users/sophieso/Documents/Workspace/ColorMatcher/color-mapping.json') as f:
      self.data = json.load(f)


def main():
  filePaths = searchSwiftFiles()

  allElements = []
  for index, path in enumerate(filePaths):
    print('Analyzing {0}...{1}/{2}'.format(path, index + 1, len(filePaths)))
    
    elementDict = findUIElements(path)
    if elementDict:
      allElements.append(elementDict)

  jsonFile = open('/Users/sophieso/Documents/Workspace/ColorMatcher/change-log-for-marketplace.json', 'w+')
  json.dump(allElements, jsonFile)
  jsonFile.close()
    

def searchSwiftFiles():
  basePath = '/Users/sophieso/Documents/Workspace/TKPlanner-iOS'
  searchPaths = [
    # '/App/Dashboard/**/*.swift',    - Done
    # '/App/Launch/**/*.swift',       - Done
    '/App/Vendors/**/*.swift',
    '/VendorUI/**/*.swift',
    '/VendorUtilities/**/*.swift',
    # '/GuestServices/**/*.swift',
    # '/Utilities/**/*.swift',
    # '/WeddingCountdown/**/*.swift',
  ]

  filePaths = []
  for sarchPath in searchPaths:
    result = glob.glob(basePath + sarchPath, recursive=True)
    filePaths += result
  
  return filePaths

def findUIElements(filePath):
  elementList = ElementList()
  with open(filePath) as f:
    read_data = f.read()
    f.closed

    elementList.icons = findIcons(read_data)
    elementList.textColors = findColors(ElementPattern.textColorPattern, read_data)
    elementList.linkColors = findColors(ElementPattern.linkColorPattern, read_data)
    elementList.borderColors = findColors(ElementPattern.borderColorPattern, read_data)
    elementList.backgroundColors = findColors(ElementPattern.backgroundColorPattern, read_data)
    elementList.attributedStringColors = findColors(ElementPattern.attributedStringColorPattern, read_data)

    mapping = ColorMapping()
    matchIconColors(elementList.icons, mapping)
    matchColors(elementList.textColors, mapping.data['text'])
    matchColors(elementList.linkColors, mapping.data['link'])
    matchColors(elementList.borderColors, mapping.data['border'])
    matchColors(elementList.backgroundColors, mapping.data['backgrounds'])
    matchColors(elementList.attributedStringColors, mapping.data['text'])

  updateAllColors(read_data, elementList, filePath)

  if elementList.totalElementCount() > 0:
    elementDict = {'file': filePath, 'icons': elementList.icons, 'textColors': elementList.textColors, 'linkColors': elementList.linkColors, 'borderColors': elementList.borderColors, 'backgroundColors': elementList.backgroundColors, 'attributedStringColors': elementList.attributedStringColors}
    return elementDict
    
def updateAllColors(data, elementList, filePath):
  updatedData = data
  updatedData = updateIconColors(elementList.icons, updatedData)
  updatedData = updateColors('(\S*textColor\s*=\s*)(UIColor)*(\.)', elementList.textColors, updatedData)
  updatedData = updateColors('(\S*setTitleColor\()(UIColor)?(\.)', elementList.linkColors, updatedData)
  updatedData = updateColors('(\S*borderColor\s*=\s*)(UIColor)*(\.)', elementList.borderColors, updatedData)
  updatedData = updateColors('(\S*backgroundColor\s*=\s*)(UIColor)*(\.)', elementList.backgroundColors, updatedData)
  updatedData = updateColors('(.*foregroundColor\s*:\s*)(UIColor)?(\.)', elementList.attributedStringColors, updatedData)

  with open(filePath, 'w') as f:
    f.write(updatedData)

def findColors(pattern, data):
  colors = []
  result = pattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[3]) > 0:
      colors.append({'item': ''.join(item), 'color': item[3]})
    
  return colors

def matchColors(elements, mapping):
  for item in elements:
    originalColor = item['color']
    newColor = ''

    if originalColor in mapping:
      newColor = mapping[originalColor]

    item['color'] = {'original': originalColor, 'new': newColor}

def updateColors(patternString, elements, data):
  updatedData = data
  for item in elements:
    colorDict = item['color']
    originalColor = colorDict['original']
    newColor = colorDict['new']

    if len(newColor) > 0:
      pattern = re.compile(r'%s%s' %(patternString, originalColor))
      updatedData = pattern.sub(r'\1\2\3%s' %newColor, updatedData)

  return updatedData

# icon handlers
def findIcons(data):
  icons = []
  result = ElementPattern.iconPattern.findall(data)
  for item in result:
    code = ''.join(item)
    color = []
    element = ''

    if len(item) > 0 and len(item[0]) > 0:
      iconColor = searchIconColor(code)
      if iconColor:
        color.append(iconColor)
      else:
        element = findIconElements(item[0])
        if element:
          color = searchIconTintColor(element, data)

    icons.append({'item': code, 'element': element, 'color': color})
    
  return icons

def searchIconColor(data):
  result = ElementPattern.iconColorPattern.search(data)
  if result:
    groups = result.groups()
    if len(groups) > 3 and len(groups[3]) > 0:
      return groups[3]

def findIconElements(data):
  result = ElementPattern.iconElementPattern.search(data)
  if result:
    groups = result.groups()
    if len(groups) > 0 and len(groups[0]) > 0:
      return groups[0]

def searchIconTintColor(element, fileData):
  colors = []
  pattern = re.compile(r'(%s\?*.tintColor\s*=\s*)(UIColor)?(\.)(\w+)' %element)
  result = pattern.findall(fileData)
  for item in result:
    if len(item) > 3 and len(item[3]) > 0:
      colors.append(item[3])

  return colors

def matchIconColors(elements, mapping):
  iconsMapping = mapping.data['icons']
  for item in elements:
    matchedColors = []

    for color in item['color']:
      originalColor = color
      newColor = ''

      if originalColor in iconsMapping:
        newColor = iconsMapping[originalColor]

      matchedColors.append({'original': originalColor, 'new': newColor})

    item['color'] = matchedColors

def updateIconColors(elements, data):
  updatedData = data
  for item in elements:
    element = item['element']

    for color in item['color']:
      originalColor = color['original']
      newColor = color['new']

      if len(newColor) > 0:
        iconPattern = re.compile(r'(tinted\(\s*|color:\s*)(UIColor)*(\.)*%s' %originalColor)
        updatedData = iconPattern.sub(r'\1\2\3%s' %newColor, updatedData)

        tintPattern = re.compile(r'(%s\?*.tintColor\s*=\s*)(UIColor)?(\.)%s' %(element, originalColor))
        updatedData = tintPattern.sub(r'\1\2\3%s' %newColor, updatedData)

  return updatedData

# cell handlers
def findCells(data):
  cells = []
  result = ElementPattern.cellPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[1]) > 0:
      cells.append(item[1])
    
  return cells

# controller handlers
def matchControllers(data):
  controllers = []
  result = ElementPattern.controllerPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[1]) > 0:
      controllers.append(item[1])
    
  return controllers

main()
